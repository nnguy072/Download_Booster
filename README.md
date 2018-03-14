# HTTP Proxy

----
## AUTHORS
Nam Nguyen, Rodney Ho, Neel Sethia

----
## Usage
1. Clone repo and navigate into directory
2. Run HTTP Proxy via "python PythonProxy.py"
3. Open another terminal and try "curl -x localhost:8080 <URL>*

*Note only works for websites with "http"


----
## Examples
* curl -O --x localhost:8080 http://cdn1-www.dogtime.com/assets/uploads/gallery/samoyed-dogs-and-puppies/samoyed-dogs-puppies-1.jpg
* curl -O --proxy localhost:8080 http://www.hanedanrpg.com/photos/hanedanrpg/12/55932.jpg