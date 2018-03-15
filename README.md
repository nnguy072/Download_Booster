# HTTP Proxy

## AUTHORS
Nam Nguyen, Rodney Ho, Neel Sethia

## How to Run
1. Fork/Clone repo and cd into directory
2. Open up two terminals:
3. Do these commands (change if host/port if needed): 

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