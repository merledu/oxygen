# Oxygen: A RISC-V Simulator
Oxygen is a RISC-V assembly simulator built with a Django backend. It supports the I, M, F and C extensions, allowing users to write, decode, and execute RISC-V assembly programs. The simulator provides both full program execution and step-by-step execution modes, with features to display and update register and memory values accordingly.

## Features
- Write RISC-V assembly code.
- Support for I, M, F, and C extensions.
- Instruction decoding.
- Hexadecimal representation of each instruction.
- Full program processing in one go.
- Step-by-step execution.
- Display and update register and memory values during execution.

## Getting Started
1. Clone the repository.
   ```sh
   git clone --recursive https://github.com/merledu/oxygen.git
   cd oxygen
   ```
2. Setup the application.
    - Distro dependencies
        - Debian
          ```sh
          sudo apt install device-tree-compiler libboost-regex-dev libboost-system-dev python3.10
          ```
        - Arch
          ```sh
          sudo pacman -S --needed dtc boost boost-libs python
          ```
    - Repo setup
      ```sh
      # Directories
      mkdir tmp tools

      # Create virtual environment and source it
      python3 -m venv .venv
      source .venv/bin/activate
      pip3 install Django pexpect

      # Install toolchain
      wget -O- https://github.com/riscv-collab/riscv-gnu-toolchain/releases/download/2024.08.06/riscv32-elf-ubuntu-22.04-gcc-nightly-2024.08.06-nightly.tar.gz | tar -xzf -
      mv riscv tools/riscv32-gnu-toolchain
      wget -O- https://github.com/riscv-collab/riscv-gnu-toolchain/releases/download/2024.08.06/riscv64-elf-ubuntu-22.04-gcc-nightly-2024.08.06-nightly.tar.gz | tar -xzf -
      mv riscv tools/riscv64-gnu-toolchain

      # Environment variables
      export OXYGEN_ROOT=`pwd`
      export SPIKE=$OXYGEN_ROOT/tools/spike

      # Install spike
      cd tools_submodules/riscv-isa-sim
      mkdir build
      cd build
      ../configure --prefix=$SPIKE
      make
      make install
      cd ../../..
      ```
3. Run the development server.
   ```sh
   python3.10 manage.py runserver
   ```
   The server will start on `http://127.0.0.1:8000/`.

## Usage
1. Open your web browser and navigate to `http://127.0.0.1:8000/`.
2. You can start writing RISC-V assembly code in the provided text editor.
3. After which you can use the following features:
   - **Assemble:** Get the hex representation and base instruction of each instruction.
   - **Run:** Execute the entire program at once.
   - **Step Execution:** Execute the program instruction by instruction.
   - **Reset:** Reset the memory and registers to start executing again.
   - **Registers and Memory:** View and update register and memory values as instructions are executed.
