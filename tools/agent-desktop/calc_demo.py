# Drive gnome-calculator through agent-desktop: snapshot -> click refs -> verify result.
import json, subprocess, sys
def ad(*a):
    return json.loads(subprocess.run(["agent-desktop",*a],capture_output=True,text=True).stdout)
def walk(n,out):
    if isinstance(n,dict):
        out.append(n); [walk(c,out) for c in n.get("children",[])]
    return out
snap=ad("snapshot","--app","gnome-calculator","-i")
nodes=walk(snap["data"]["tree"],[])
refs={n["name"]:n["ref_id"] for n in nodes if n.get("role")=="button" and "name" in n}
expr=sys.argv[1]  # e.g. "180+96+242="
for ch in expr:
    name={"+":"+","-":"−","*":"×","=":"="}.get(ch,ch)
    r=ad("click",refs[name]); print(ch, "ok" if r["ok"] else r["error"]["code"])
import time; time.sleep(1.5)
after=walk(ad("snapshot","--app","gnome-calculator")["data"]["tree"],[])
for n in after:
    if n.get("role") in ("textfield","listbox","listitem","label") and (n.get("value") or n.get("name")):
        print("LEIDO:", n.get("role"), n.get("name"), n.get("value"))
