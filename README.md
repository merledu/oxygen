# Oxygen RISC-V Simulator
Oxygen is a RISC-V assembly simulator built with a Django backend. It supports the I, M, F, and C extensions, allowing users to write, decode, and execute RISC-V assembly programs. The simulator provides both full program execution and step-by-step execution modes, with features to display and update register and memory values accordingly.


## Features
- Write RISC-V assembly code
- Support for I, M, F, and C extensions
- Instruction decoding
- Hexadecimal representation of each instruction
- Full program processing in one go
- Step-by-step execution
- Display and update register and memory values during execution


## Getting Started
### Prerequisites
```sh
sudo apt install python3 git
```


### Installation
1. **Clone the repository:**
    ```sh
    git clone https://github.com/merledu/oxygen.git
    cd oxygen
    ```
2. **Create and activate a virtual environment:**
    ```sh
    python -m venv .venv
    source .venv/bin/activate
    pip3 install django
    ```
3. **Run the development server:**
    ```sh
    python manage.py runserver
    ```
    The server will start on `http://127.0.0.1:8000/`.


### Usage
1. Open your web browser and navigate to `http://127.0.0.1:8000/`.
2. You can start writing RISC-V assembly code in the provided text editor.
3. After which you can use the following features:
    - **Assemble:** Get the hex representation and base instruction of each instruction.
    - **Run:** Execute the entire program at once.
    - **Step Execution:** Execute the program instruction by instruction.
    - **Reset:** Reset the memory and registers to start executing again.
    - **Registers and Memory:** View and update register and memory values as instructions are executed.
