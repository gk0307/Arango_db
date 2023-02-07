#!/usr/bin/env python
from contextlib import asynccontextmanager
import logging
import os
from typing import Optional

from fastapi import FastAPI
from arango import ArangoClient
from starlette.responses import FileResponse


PATH = os.path.dirname(os.path.abspath(__file__))
#print("PATH",PATH)

app = FastAPI()
port = os.getenv("PORT", 8080)
client = ArangoClient(hosts='http://18.210.74.110:8529/')
db = client.db('urovant', username='root', password='dataaces')



@asynccontextmanager
async def get_db():
        yield db


@app.get("/")
async def get_index():
    return FileResponse(os.path.join(PATH, "static", "in.html"))


def serialize_payer(payer):
    #print(payer)
    return {
        "PAYER_ENTITY_ID": payer["PAYER_ENTITY_ID"],
        "BOB_ID": payer["BOB_ID"],
        "title":payer["PAYER_ENTITY"],
        "BOB":payer["BOB"],
        "label":"payer"
        
        # "ENTERPRISE": payer["ENTERPRISE"],
        # "ENTERPRISE_ID": payer["ENTERPRISE_ID"],
    }
def serialize_enterprise(enterprise):
    return{
        "title": enterprise["ENTERPRISE"],
         "ENTERPRISE_ID": enterprise["ENTERPRISE_ID"],
         "label":"enterprise"
    }

# @app.get("/graph")
# async def get_graph(results):
#     async with get_db() as dbs:
#         results = dbs.aql.execute("FOR s in L3_payer limit 100 RETURN s")
#         nodes = []
#         rels = []
#         i=0
#         for record in results:
#             #print("record" , record["_key"])
#             payer = {"title": record["PAYER_ENTITY_ID"], "label": "payer"}
#             try:
#                 target = nodes.index(payer)
#             except ValueError:
#                 nodes.append(payer)
#                 target = i
#                 i += 1
#             enterprise = {"title": record["ENTERPRISE_ID"], "label": "enterprise"}
#             try:
#                 source = nodes.index(enterprise)
#             except ValueError:
#                 nodes.append(enterprise)
#                 source = i
#                 i += 1
#             rels.append({"source": source, "target": target})
#             #print("source:", source, "Destination",target)
#         return {"nodes": nodes, "links": rels}

#@app.get("/graph")
def get_graph(results):
   
    nodes = []
    rels = []
    payers=[]
    i=0
    for r in results:
        print(r)
        payer = {"title": r["PAYER_ENTITY"], "label": "payer"}
        p=serialize_payer(r)
        payers.append(p)
        try:
            target = nodes.index(payer)
        except ValueError:
            nodes.append(payer)
            target = i
            i += 1
        enterprise = {"title": r["ENTERPRISE"], "label": "enterprise"}
        #enterprise = serialize_enterprise(r)
        try:
            source = nodes.index(enterprise)
        except ValueError:
            nodes.append(enterprise)
            source = i
            i += 1
        rels.append({"source": source, "target": target})
        print("source", source, "target",target)
    return {"nodes": nodes, "links": rels,"payers":payers}

@app.get("/search")
async def get_search(e: str = None, p: str = None):
    # print("length of q is "+len(q))
    # print("Enterprise is given as ")
    print(str(e)+" IS Enterprise and "+str(p)+" is Payer")
    if len(str(e)) == 0 and len(str(p)) == 0:
        print("Both e and p are None..")
        async with get_db() as dbs:
            results = dbs.aql.execute("FOR s in L3_payer RETURN s")
            print(results)
            return get_graph(results)
    #         return [serialize_payer(record) for record in results]
    if len(str(e))>0 and len(str(p))==0:
        print("only p is None")
        async with get_db() as dbs:
            results = dbs.aql.execute("FOR s in L3_payer FILTER s.ENTERPRISE==@enterprise RETURN s",bind_vars={"enterprise":e})
            print(results)
            return get_graph(results)
            #return [serialize_payer(record) for record in results]
    if len(str(e))>0 and len(str(p))>0:
        print("both e and p are NOT none")
        async with get_db() as dbs:
            results = dbs.aql.execute("FOR s in L3_payer FILTER s.ENTERPRISE==@enterprise && s.PAYER_ENTITY==@payer RETURN s",bind_vars={"enterprise":e, "payer":p})
            print(results)
            return get_graph(results)
            #return [serialize_payer(record) for record in results]        

if __name__ == "__main__":
    import uvicorn

    logging.root.setLevel(logging.INFO)
    logging.info("Starting on port %d, database is at %s", port, client)

    uvicorn.run(app, port=port)