from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ipv4, tcp, udp, icmp
import numpy as np
import time
import datetime
import tflite_runtime.interpreter as tflite
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
from pathlib import Path
import os

class DDoSCNNController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(DDoSCNNController, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.flow_stats = {}

        self.interpreter = tflite.Interpreter(model_path="/home/ryu/cnn_ddos_model.tflite")
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

        env_path = Path(__file__).resolve().parent / ".env"
        load_dotenv(dotenv_path=env_path)
        self.email_user = os.getenv("EMAIL_USER")
        self.email_pass = os.getenv("EMAIL_PASS")
        self.email_to = os.getenv("EMAIL_TO")

    def send_email_alert(self, src_ip, dst_ip):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        body_text = f"DDoS attack detected from {src_ip} to {dst_ip} [{timestamp}]"
        msg = MIMEText(body_text, _charset="utf-8")
        msg["Subject"] = "DDoS Alert from Ryu System"
        msg["From"] = self.email_user
        msg["To"] = self.email_to

        try:
            server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
            server.login(self.email_user, self.email_pass)
            server.send_message(msg)
            server.quit()
            print("[INFO] Alert email sent successfully.")
        except Exception as e:
            print("[ERROR] Failed to send email:", e)

    def predict(self, features):
        input_data = np.expand_dims(np.array(features, dtype=np.float32), axis=0)
        input_data = np.expand_dims(input_data, axis=-1)
        self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
        self.interpreter.invoke()
        output_data = self.interpreter.get_tensor(self.output_details[0]['index'])
        predicted_class = int(np.argmax(output_data))
        print("[DEBUG] Predict:", output_data.tolist(), "->", predicted_class)
        return predicted_class

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        parser = datapath.ofproto_parser
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(datapath.ofproto.OFPP_CONTROLLER, datapath.ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None, idle_timeout=0, hard_timeout=0):
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod_args = {
            "datapath": datapath,
            "priority": priority,
            "match": match,
            "idle_timeout": idle_timeout,
            "hard_timeout": hard_timeout,
            "instructions": inst
        }
        if buffer_id:
            mod_args["buffer_id"] = buffer_id
        mod = parser.OFPFlowMod(**mod_args)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto
        in_port = msg.match["in_port"]
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        if eth is None:
            return

        if eth.ethertype == 0x0806:
            actions = [parser.OFPActionOutput(ofproto.OFPP_FLOOD)]
            out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id, in_port=in_port, actions=actions,
                                      data=msg.data if msg.buffer_id == ofproto.OFP_NO_BUFFER else None)
            datapath.send_msg(out)
            return

        if eth.ethertype != 0x0800:
            return

        ip = pkt.get_protocol(ipv4.ipv4)
        if ip is None:
            return

        src_ip = ip.src
        dst_ip = ip.dst
        proto = ip.proto

        tcp_pkt = pkt.get_protocol(tcp.tcp)
        udp_pkt = pkt.get_protocol(udp.udp)
        icmp_pkt = pkt.get_protocol(icmp.icmp)

        tp_src = tcp_pkt.src_port if tcp_pkt else (udp_pkt.src_port if udp_pkt else 0)
        tp_dst = tcp_pkt.dst_port if tcp_pkt else (udp_pkt.dst_port if udp_pkt else 0)
        icmp_type = icmp_pkt.type if icmp_pkt else 0
        icmp_code = icmp_pkt.code if icmp_pkt else 0

        now = time.time()
        key = (src_ip, dst_ip)
        stat = self.flow_stats.get(key, {"start_time": now, "packet_count": 0, "byte_count": 0})
        stat["packet_count"] += 1
        stat["byte_count"] += len(msg.data)
        duration = now - stat["start_time"] or 1e-6
        self.flow_stats[key] = stat

        features = [
            float(tp_src), float(tp_dst), float(proto),
            float(icmp_code), float(icmp_type),
            duration, duration * 1e9,
            0.0, 0.0, 0.0,
            float(stat["packet_count"]),
            float(stat["byte_count"]),
            float(stat["packet_count"] / duration),
            float(stat["byte_count"] / duration),
            float(stat["byte_count"] / (duration * 1e9))
        ]

        if stat["packet_count"] < 5 or duration < 0.5:
            return

        label = self.predict(features)
        if label == 1:
            print(f"[INFO] DDoS detected from {src_ip} to {dst_ip} - BLOCK")
            with open("ddos_log.txt", "a") as f:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{timestamp}] DDoS detected from {src_ip} to {dst_ip}\n")
            with open("blocked_ip.txt", "a+") as f:
                f.seek(0)
                blocked_ips = f.read().splitlines()
                if src_ip not in blocked_ips:
                    f.write(src_ip + "\n")
                    self.send_email_alert(src_ip, dst_ip)
            match = parser.OFPMatch(eth_type=0x0800, ipv4_src=src_ip)
            actions = []
            self.add_flow(datapath, 10, match, actions, idle_timeout=60)
            return

        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})
        self.mac_to_port[dpid][eth.src] = in_port
        out_port = self.mac_to_port[dpid].get(eth.dst, ofproto.OFPP_FLOOD)
        actions = [parser.OFPActionOutput(out_port)]
        out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=msg.buffer_id,
            in_port=in_port,
            actions=actions,
            data=msg.data if msg.buffer_id == ofproto.OFP_NO_BUFFER else None
        )
        datapath.send_msg(out)
