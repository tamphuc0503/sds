https://konghq.com/blog/engineering/custom-lua-plugin-kong-gateway

# Plugin-based Architecture
- Kong API Gateway is built on OpenResty, which extends the NGINX proxy server to run Lua scripts. It sits as a proxy between a client’s requests and routes them to defined services.
- Kong uses plugins to extend features such as auth, rate limit, caching, logging, security, transformations

# Plugin Execution model: 
- rewrite: modify request
- access: auth, rate limit
- balancer: upstream selection
- header_filter: modify response headers
- body_filter: modify response body
- log: logging, metrics

# Investigate container kong
- plugin path: /usr/local/share/lua/5.1/kong/plugins
- configuration kong: /usr/local/kong
- kng KING module (most importantant):  global.lua
# Debugging in vscode