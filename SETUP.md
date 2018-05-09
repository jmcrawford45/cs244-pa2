###Setup Instructions
- Open a VM instance in Google Cloud Platform Console (I used 8v CPUs, 30GB, 
and Debian GNU/Linux 9 (stretch) image, default for everything else.)
- Install dependencies
```
sudo apt-get update
sudo apt-get install git-core python-matplotlib
```
- Setup Mininet
```
git clone git://github.com/mininet/mininet
cd mininet
git checkout -b 2.2.1 2.2.1
cd ..
mininet/util/install.sh -nfv
```
- Pip setup
```
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python get-pip.py
git clone https://github.com/jmcrawford45/cs244-pa2/
cd cs244-pa2/pox/pox/ext
sudo python build_topology.py
```
