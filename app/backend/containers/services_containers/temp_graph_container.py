from dependency_injector import containers, providers

from boiler.temp_graph.repository.temp_graph_simple_repository import TempGraphSimpleRepository
from boiler_softm.temp_graph.parsers.soft_m_json_temp_graph_parser import SoftMJSONTempGraphParser
from boiler_softm.temp_graph.repository.online_soft_m_temp_graph_repository import OnlineSoftMTempGraphRepository
from backend.services.temp_graph_update_service.simple_temp_graph_update_service import SimpleTempGraphUpdateService


class TempGraphContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    temp_graph_parser = providers.Singleton(SoftMJSONTempGraphParser)

    temp_graph_src_repository = providers.Singleton(OnlineSoftMTempGraphRepository,
                                                    temp_graph_parser=temp_graph_parser)

    temp_graph_repository = providers.Singleton(TempGraphSimpleRepository)

    temp_graph_update_service = providers.Singleton(SimpleTempGraphUpdateService,
                                                    temp_graph_src_repository=temp_graph_src_repository,
                                                    temp_graph_repository=temp_graph_repository)
