from lusid.extensions import (
    ApiClientFactory,
    SyncApiClientFactory,
    EnvironmentVariablesConfigurationLoader,
)
from lusid.api import ApplicationMetadataApi
import pytest


def test_get_application_metadata_sync():
    api_client_factory = SyncApiClientFactory(
        app_name="test_sdk",
        config_loaders=[EnvironmentVariablesConfigurationLoader()],
        tcp_keep_alive=False
    )
    with api_client_factory:
        api_instance = api_client_factory.build(ApplicationMetadataApi)
        response = api_instance.get_lusid_versions_with_http_info()
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_application_metadata_async():
    api_client_factory = ApiClientFactory(
        app_name="test_sdk",
        config_loaders=[EnvironmentVariablesConfigurationLoader()]
    )
    async with api_client_factory:
        api_instance = api_client_factory.build(ApplicationMetadataApi)
        response = await api_instance.get_lusid_versions_with_http_info()
        assert response.status_code == 200
