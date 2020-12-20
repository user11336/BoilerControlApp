from dependency_injector import containers, providers

from boiler_t_predictor_service import BoilerTPredictorService
from temp_graph_service.file_temp_graph_service import FileTempGraphService
from weather_forecast_service import WeatherForecastService
from resources.home_time_deltas_resource import HomeTimeDeltasResource
from resources.optimized_t_table_resource import OptimizedTTableResource


class Services(containers.DeclarativeContainer):
    config = providers.Configuration()

    logging = providers.DependenciesContainer()

    optimized_t_table = providers.Resource(
        OptimizedTTableResource,
        config.boiler_t_prediction_service.optimized_t_table_path
    )

    homes_time_deltas = providers.Resource(
        HomeTimeDeltasResource,
        config.boiler_t_prediction_service.homes_deltas_path
    )

    temp_graph_service = providers.Singleton(
        FileTempGraphService.create_service,
        config.boiler_t_prediction_service.t_graph_path
    )

    weather_forecast_service = providers.Singleton(
        WeatherForecastService,
        server_timezone=config.weather_forecast_service.server_timezone,
        server_address=config.weather_forecast_service.server_address,
        update_interval=config.weather_forecast_service.update_interval
    )

    boiler_t_predictor_service = providers.Singleton(
        BoilerTPredictorService.create_service,
        optimized_t_table=optimized_t_table,
        home_time_deltas=homes_time_deltas,
        temp_graph_service=temp_graph_service,
        home_t_dispersion_coefficient=config.boiler_t_prediction_service.home_t_dispersion_coefficient,
        weather_forecast_service=weather_forecast_service
    )