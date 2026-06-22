# Mock MCP Server for Salesforce Agentforce

A minimal, verified Model Context Protocol server you can register in the
Agentforce MCP Registry. It uses the **Streamable HTTP** transport (required by
Salesforce) and exposes four mock retail/logistics tools that return
deterministic fake data, so demos are repeatable.

Tools: `find_where_to_buy`, `check_online_availability`, `get_product_details`.

---

## Run locally (macOS / zsh)

```zsh
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python server.py
```

In a second terminal:

```zsh
curl http://127.0.0.1:8787/health
```

Expect `ok`. The MCP endpoint is `http://127.0.0.1:8787/mcp`.

### Environment variables (all optional)
| Var | Default | Purpose |
|-----|---------|---------|
| `PORT` / `MCP_PORT` | `8787` | Listen port (`PORT` is injected by Render) |
| `MCP_HOST` | `0.0.0.0` | Bind address |
| `MCP_API_KEY` | _(unset)_ | If set, requires `Authorization: Bearer <key>` on every request |

---

## Deploy to Render (Hobby workspace + Free compute = $0)

Free compute spins down after 15 min idle and cold-starts in ~30-60s. Fine for
testing; switch `plan: free` to `plan: starter` in `render.yaml` ($7/mo) for an
always-warm demo.

1. Push this folder to a GitHub repo:
   ```zsh
   git init
   git add server.py requirements.txt render.yaml .gitignore README.md
   git commit -m "mock mcp server"
   git branch -M main
   git remote add origin https://github.com/<you>/mock-mcp.git
   git push -u origin main
   ```
2. dashboard.render.com (Hobby workspace) -> New -> Blueprint -> connect the
   repo. Render reads `render.yaml` and creates the service.
3. Apply, wait for Live (green). URL looks like
   `https://mock-retail-mcp.onrender.com`.
4. Verify:
   ```zsh
   curl https://mock-retail-mcp.onrender.com/health
   ```

---

## Register in Salesforce

Prerequisites: an Agentforce-enabled org and an existing Agentforce Service or
Employee agent.

1. **Set the planner type.** MCP tools require the concurrent multi-agent
   orchestrator. Find the planner:
   ```zsh
   sf data query --query "SELECT Id, PlannerType, DeveloperName FROM GenAiPlannerDefinition" --use-tooling-api
   ```
   Set your agent's `PlannerType` to `Atlas__ConcurrentMultiAgentOrchestration`
   via Workbench / Tooling API / `sf` (it's a setup object, so anonymous Apex
   DML won't work). Some orgs expose this as a toggle in Agent Builder.

2. **Warm the service** if on free compute: open the `/health` URL in a browser
   so it's awake before registering.

3. **Register.** Setup -> Agentforce Registry -> New -> paste
   `https://<host>/mcp` -> auth None (or Bearer if `MCP_API_KEY` is set) ->
   select tools. Each tool becomes an Asset Library action and a permission set
   is generated -- assign that permission set to the agent's user.

4. **Attach.** Agentforce Builder -> open agent -> Topic -> This Topic's Actions
   -> New -> Add from Asset Library -> select the tool(s).

5. **Test.** Prompt: "Where can I buy Heinz Tomato Ketchup near K1B?" Watch
   Render logs for `POST /mcp 200 OK`. Debug via `mcp_request` / `mcp_response`
   in the action detail.

---

## Notes

- Runs stateless with JSON responses (`stateless_http=True`,
  `json_response=True`) for maximum compatibility with enterprise clients and
  proxies -- no SSE session affinity required.
- Tool descriptions are what the Atlas reasoning engine routes on. If you add
  tools, write clear "use this when..." docstrings.
- All data is fake, hash-derived from inputs, so the same request always returns
  the same response.

## Free-tier troubleshooting

- Registry wizard or first agent call times out -> service was asleep; hit
  `/health` to wake it, then retry.
- Tools never appear in the Asset Library -> planner type wasn't set to
  `Atlas__ConcurrentMultiAgentOrchestration`.
