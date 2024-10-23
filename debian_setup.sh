# Dependencies
sudo apt install device-tree-compiler libboost-regex-dev libboost-system-dev python3.10


# PATHS
export OXYGEN_ROOT=`pwd`
export TMP="$OXYGEN_ROOT/tmp"
export OXYGEN_TOOLS="$OXYGEN_ROOT/tools"
export OXYGEN_VENV="$OXYGEN_ROOT/.venv"
export OXYGEN_SUBMODULES="$OXYGEN_ROOT/tools_submodules"
export SPIKE="$OXYGEN_TOOLS/spike"


# Directories
mkdir $OXYGEN_TOOLS
mkdir $TMP


# Django
python3 -m venv .venv
source "$OXYGEN_VENV/bin/activate"
pip3 install Django


# Toolchain
wget -O- https://github.com/riscv-collab/riscv-gnu-toolchain/releases/download/2024.08.06/riscv32-elf-ubuntu-22.04-gcc-nightly-2024.08.06-nightly.tar.gz | tar -xzf -
mv riscv $OXYGEN_TOOLS/riscv32-gnu-toolchain
wget -O- https://github.com/riscv-collab/riscv-gnu-toolchain/releases/download/2024.08.06/riscv64-elf-ubuntu-22.04-gcc-nightly-2024.08.06-nightly.tar.gz | tar -xzf -
mv riscv $OXYGEN_TOOLS/riscv64-gnu-toolchain


# Spike
cd "$OXYGEN_SUBMODULES/riscv-isa-sim"
mkdir build
cd build
../configure --prefix=$SPIKE
make -j `nproc`
make install
cd $OXYGEN_ROOT

