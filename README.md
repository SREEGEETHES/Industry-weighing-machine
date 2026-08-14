How to Clone on a New Machine
If you ever need to set up on another PC:

#open powershell and run this commands

git clone https://github.com/SREEGEETHES/Industry-weighing-machine.git

cd "Industry-weighing-machine\iwp\backend"

python -m venv venv          

venv\Scripts\activate

pip install -r requirements.txt

python -m uvicorn app.main:app --reload


the above is for first time ...double click the start_demo.bat which fires up multiple terminals those are virtual printer and scale in production we can change the ip address
