# HTTP Proxy

## AUTHORS
Nam Nguyen, Rodney Ho, Neel Sethia

## How to Run
1. Fork/Clone repo and cd into directory
2. Edit PythonProxy for your devices:
  --* Go to the ```_connect_target()``` function
  --* Change following code to match your devices
  ```
  self.target = socket.socket(soc_family)
  self.target.bind(('123.456.789.10',0)) #device 1
  self.target.connect(address)

  #TODO: change for different interfaces i.g. wifi & ethernet
  self.target2 = socket.socket(soc_family)
  self.target2.bind(('123.456.789.10',0)) #device 2
  self.target2.connect(address)
  ```
3. Open two terminals
4. Do these commands (change if host/port if needed):

Terminal 1:
```
python PythonProxy.py;
```

Terminal 2*:
```
curl -x localhost:8080 <URL>
```
*Note only works for websites with "http"


----
## Examples
* curl -O --x localhost:8080 http://cdn1-www.dogtime.com/assets/uploads/gallery/samoyed-dogs-and-puppies/samoyed-dogs-puppies-1.jpg
* curl -O --proxy localhost:8080 http://www.hanedanrpg.com/photos/hanedanrpg/12/55932.jpg