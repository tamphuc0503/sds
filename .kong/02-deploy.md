# Kong Docker
## Kong components
Ports of kong: expose 8001 and 8000 
   - 8001: ports to call Kong API services. Developer can POST payload to this port to create a new service and route to point to that service.
      - Create new httpbin service via Kong API
      ```
      curl -i -X POST http://localhost:8001/services \
      --data name=httpbin \
      --data url=https://httpbin.org
      ```
      - Create new route to handle request sent to Kong
      ```
      curl -i -X POST http://localhost:8001/services/httpbin/routes \
      --data paths[]=/test
      ```
   - 8000: port that Kong will listen requests.
      - After create service and route, we can call this service with 
      ```
      curl http://localhost:8000/test/get
      ```
      - This means: Kong resolve "http://localhost:8000/test" to host https://httpbin.org with path "get"
   - 8002: port to open Kong Manager.
- Admin portal of kong
## Db Mode
- docker network create kong-net
- run kong-db
```
docker run -d --name kong-db \
  --network=kong-net \
  -e POSTGRES_USER=kong \
  -e POSTGRES_PASSWORD=kong \
  -e POSTGRES_DB=kong \
  postgres:15
```
- create kong migrations to migrate database to kong-db
```
docker run --rm \
  --network=kong-net \
  -e KONG_DATABASE=postgres \
  -e KONG_PG_HOST=kong-db \
  -e KONG_PG_USER=kong \
  -e KONG_PG_PASSWORD=kong \
  kong/kong:3.6 kong migrations bootstrap
```
- start kong gateway and manager (port 8002)
```
docker run -d --name kong \
  --network=kong-net \
  -e KONG_DATABASE=postgres \
  -e KONG_PG_HOST=kong-db \
  -e KONG_PG_USER=kong \
  -e KONG_PG_PASSWORD=kong \
  -e KONG_PROXY_ACCESS_LOG=/dev/stdout \
  -e KONG_ADMIN_ACCESS_LOG=/dev/stdout \
  -e KONG_PROXY_ERROR_LOG=/dev/stderr \
  -e KONG_ADMIN_ERROR_LOG=/dev/stderr \
  -e KONG_ADMIN_LISTEN=0.0.0.0:8001 \
  -p 8000:8000 \
  -p 8001:8001 \
  -p 8002:8002 \
  kong/kong:3.6
```
- Call Kong Admin API to create service and route then Ctrl+F5 to view in Kong Manager.
## Db less
- create a db-less kong gateway
```
docker run -d --name kong \
  -e KONG_DATABASE=off \
  -e KONG_DECLARATIVE_CONFIG=/kong/kong.yaml \
  -v $(pwd)/kong.yaml:/kong/kong.yaml \
  -p 8000:8000 \
  -p 8001:8001 \
  -p 8002:8002 \
  kong/kong:3.6
```
- issue: unable to curl 8001 because we don't expose ADMIN_LISTEN=0.0.0.0:8001 
so we can fix by adding  -e KONG_ADMIN_LISTEN=0.0.0.0:8001
```
docker run -d --name kong \
  -e KONG_DATABASE=off \
  -e KONG_DECLARATIVE_CONFIG=/kong/kong.yml \
  -e KONG_ADMIN_LISTEN=0.0.0.0:8001 \
  -v $(pwd)/kong.yml:/kong/kong.yml \
  -p 8000:8000 \
  -p 8001:8001 \
  -p 8002:8002 \
  kong/kong:3.6
```