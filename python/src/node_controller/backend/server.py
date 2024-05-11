import logging
import pathlib

import aiocron
import fastapi

import src.common.models.web as common_models
import src.common.backend.db as database
import src.node_controller.backend.services as services
import src.node_controller.backend.repositories as repositories
import src.node_controller.models.web as models
import src.node_controller.models.db as db_models

app = fastapi.FastAPI()
db_name = str(
    pathlib.Path(__file__).parent.parent / 'db' / 'node_controller.sqlite',
)
print(db_name)
db = database.DB(db_name=db_name, base=db_models.Base)
node_repository = repositories.NodeRepository(db)
node_service = services.NodeService(node_repository)


@app.get('/nodes/ping')
async def ping():
    return {'status': 'success'}


@app.post('/nodes/active')
async def nodes_active() -> models.Nodes:
    nodes = node_service.get_active_nodes()
    return models.Nodes(nodes=[models.Node.from_core(node) for node in nodes])


@app.post('/nodes/exchange')
async def nodes_exchange(
    request: models.ExchangeRequest,
) -> models.ExchangeResponse:
    nodes = node_service.exchange_nodes(
        nodes=[node.to_core() for node in request.nodes],
    )
    return models.ExchangeResponse(
        nodes=[models.Node.from_core(node) for node in nodes]
    )


@app.post('/nodes/join')
async def nodes_join(request: models.JoinRequest) -> models.JoinResponse:
    new_node = node_service.create_node(
        ipv4_address=request.ip,
        port=request.port,
        role=request.role,
    )
    return models.JoinResponse(node_uid=new_node.node_uid)


@app.post('/nodes/leave')
async def nodes_leave(request: models.LeaveRequest) -> models.LeaveResponse:
    node_service.delete_node(request.node_uid)
    return models.LeaveResponse(
        status=common_models.ResponseStatus.SUCCESS,
        message='node with given uid has been excluded from cluster',
    )


@app.post('/nodes/enable')
async def nodes_enable(request: models.EnableRequest) -> models.EnableResponse:
    node_service.enable_node(
        node_uid=request.node_uid,
        ipv4_address=request.ip,
        port=request.port,
    )
    return models.EnableResponse(status=common_models.ResponseStatus.SUCCESS)


@app.post('/nodes/disable')
async def nodes_disable(
    request: models.DisableRequest,
) -> models.DisableResponse:
    node_service.disable_node(node_uid=request.node_uid)
    return models.DisableResponse(status=common_models.ResponseStatus.SUCCESS)


@aiocron.crontab('* * * * *')
async def ping_active_nodes():
    await node_service.update_nodes_status()


if __name__ == '__main__':
    import uvicorn

    ping_active_nodes.start()
    uvicorn.run(app)
