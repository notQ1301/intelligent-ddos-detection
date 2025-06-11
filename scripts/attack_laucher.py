from mininet.net import Mininet
from mininet.topo import SingleSwitchTopo
from mininet.node import RemoteController
from mininet.log import setLogLevel, info
from mininet.clean import cleanup
from time import sleep
import os

def run():
    setLogLevel('info')

    info("Cleaning up Mininet before starting...\n")
    cleanup()

    num_hosts = 15
    net = Mininet(topo=SingleSwitchTopo(k=num_hosts),
                  controller=lambda name: RemoteController(name, ip='192.168.186.130'))

    net.start()

    hosts = [net.get(f'h{i}') for i in range(1, num_hosts + 1)]
    target = hosts[0]  # h1 is the target
    attackers = hosts[1:]  # h2 to h15 are attackers

    info("Host IP addresses:\n")
    for h in hosts:
        info(f"{h.name}: {h.IP()}\n")

    info("\nSending initial ARP packets to avoid packet loss...\n")
    for h in attackers:
        h.cmd(f'ping -c 1 {target.IP()}')
    sleep(1)

    info(f"\nStarting batched DDoS attack from all hosts except {target.name} to {target.IP()}\n")

    batch_size = 5
    for i in range(0, len(attackers), batch_size):
        batch = attackers[i:i+batch_size]
        for idx, h in enumerate(batch):
            if idx % 3 == 0:
                h.cmd(f'hping3 --flood -S -p 80 {target.IP()} &')
            elif idx % 3 == 1:
                h.cmd(f'hping3 --flood --udp -p 53 {target.IP()} &')
            else:
                h.cmd(f'hping3 --icmp --flood {target.IP()} &')
        info(f"Started batch {i//batch_size + 1}\n")
        sleep(5)  # wait before starting the next batch

    info("Attack in progress... Check the controller log for detection results.\n")
    input("Press Enter to stop the attack and exit...\n")

    for h in attackers:
        h.cmd('pkill hping3')

    net.stop()
    info("Stopped Mininet and ended the simulation.\n")

if __name__ == '__main__':
    run()
