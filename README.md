# debank-crawler
 
# Clone this repository
git clone https://github.com/trimstray/multitor

# Go into the repository
cd multitor

# Install
./setup.sh install

# Run the app
multitor --init 2 --user debian-tor --socks-port 9000 --control-port 9900 --proxy privoxy --haproxy


Requirements
multitor uses external utilities to be installed before running:

tor
netcat
haproxy
polipo
privoxy
http-proxy-to-socks

https://github.com/trimstray/multitor
