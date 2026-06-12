# Quick start
- mkdir /opt/fuel_qr
- copy project to /opt/fuel_qr
- echo 'export PYTHONPATH="$PYTHONPATH:/opt/fuel_qr"' >> ~/.bashrc
- source ~/.bashrc
- cd  /opt/fuel_qr &&  pip install -r requirements.txt
- export LOG_LEVEL=DEBUG # for debugging
- python app.py