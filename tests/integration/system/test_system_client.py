from typing import List

import pytest
from nisystemlink.clients.core import ApiException
from nisystemlink.clients.core._http_configuration import HttpConfiguration
from nisystemlink.clients.system import SystemClient
from nisystemlink.clients.system.models import (
    CancelJobRequest,
    CreateJobRequest,
    CreateJobResponse,
    JobSummaryResponse,
    QueryJobsRequest,
)


@pytest.fixture(scope="class")
def client(enterprise_config: HttpConfiguration) -> SystemClient:
    """Fixture to create an SystemClient instance."""
    return SystemClient(enterprise_config)


@pytest.fixture(scope="class")
def create_job(
    client: SystemClient,
):
    """Fixture to create a job."""
    responses: List[CreateJobResponse] = []

    def _create_job(job: CreateJobRequest) -> CreateJobResponse:
        response = client.create_job(job)
        responses.append(response)
        return response

    yield _create_job

    job_requests = [
        CancelJobRequest(jid=response.jid, tgt=response.tgt[0])
        for response in responses
        if response.tgt is not None
    ]

    client.cancel_jobs(job_requests)


@pytest.fixture(scope="class")
def create_multiple_jobs(
    create_job,
):
    """Fixture to create multiple jobs."""
    responses = []
    arg_1 = [["A description"]]
    arg_2 = [["Another description"]]
    tgt = ["HVM_domU--SN-ec200972-eeca-062e-5bf5-33g3g3g3d73b2--MAC-0A-E1-20-D6-96-2B"]
    fun_1 = ["system.set_computer_desc"]
    fun_2 = ["system.set_computer_asc"]
    metadata = {"queued": True, "refresh_minion_cache": {"grains": True}}
    job_1 = CreateJobRequest(
        arg=arg_1,
        tgt=tgt,
        fun=fun_1,
        metadata=metadata,
    )
    responses.append(create_job(job_1))

    job_2 = CreateJobRequest(
        arg=arg_2,
        tgt=tgt,
        fun=fun_2,
        metadata=metadata,
    )
    responses.append(create_job(job_2))

    return responses


@pytest.mark.integration
@pytest.mark.enterprise
class TestSystemClient:
    def test__create_job__one_job_created_with_right_field_values(
        self,
        create_job,
    ):
        arg = [["A description"]]
        tgt = [
            "HVM_domU--SN-ec200972-eeca-062e-5bf5-017a25451b39--MAC-0A-E1-20-D6-96-2B"
        ]
        fun = ["system.set_computer_desc"]
        metadata = {"queued": True, "refresh_minion_cache": {"grains": True}}
        job = CreateJobRequest(
            arg=arg,
            tgt=tgt,
            fun=fun,
            metadata=metadata,
        )

        response = create_job(job)

        assert response is not None
        assert response.jid is not ""
        assert response.arg == arg
        assert response.tgt == tgt
        assert response.metadata == metadata
        assert response.fun == fun
        assert response.error is None

    def test__list_jobs__list_single_job_succeeds(
        self, create_job, client: SystemClient
    ):
        arg = [["A description"]]
        tgt = [
            "HVM_domU--SN-ec200972-eeca-062e-5bf5-017a25451b39--MAC-0A-E1-20-D6-96-2B"
        ]
        fun = ["system.set_computer_desc"]
        metadata = {"queued": True, "refresh_minion_cache": {"grains": True}}
        job = CreateJobRequest(
            arg=arg,
            tgt=tgt,
            fun=fun,
            metadata=metadata,
        )
        create_job_response = create_job(job)

        response = client.list_jobs(jid=create_job_response.jid)
        assert response is not None
        assert len(response) == 1

        [response_job] = response

        assert response_job.jid == create_job_response.jid
        assert response_job.config is not None
        assert response_job.config.arg == arg
        assert response_job.config.tgt == tgt
        assert response_job.metadata == metadata
        assert response_job.config.fun == fun

    def test__list_jobs__list_multiple_jobs_succeeds(
        self, create_multiple_jobs, client: SystemClient
    ):
        response = client.list_jobs(system_id=create_multiple_jobs[0].tgt[0])
        assert len(response) == 2

    def test__list_jobs__list_multiple_jobs_take_one_succeeds(
        self, create_multiple_jobs, client: SystemClient
    ):
        response = client.list_jobs(system_id=create_multiple_jobs[0].tgt[0], take=1)
        assert len(response) == 1

    def test__list_jobs__list_multiple_jobs_skip_one_succeeds(
        self, create_multiple_jobs, client: SystemClient
    ):
        response = client.list_jobs(system_id=create_multiple_jobs[0].tgt[0], skip=1)
        assert len(response) == 1

    def test__list_jobs__invalid_system_id(self, client: SystemClient):
        response = client.list_jobs(system_id="Invalid_system_id")
        assert response == []

    def test__list_jobs__invalid_jid(self, client: SystemClient):
        response = client.list_jobs(jid="Invalid_jid")
        assert response == []

    def test__get_job_summary__returns_job_summary(self, client: SystemClient):
        response = client.get_job_summary()

        assert response is not None
        assert response.active_count is not None
        assert response.failed_count is not None
        assert response.succeeded_count is not None
        assert response.error is None

    def test__query_jobs__take_one_job_succeeds(self, client: SystemClient):
        query = QueryJobsRequest(take=1)
        response = client.query_jobs(query=query)

        assert response is not None
        assert response.data is not None
        assert len(response.data) == response.count == 1

    def test__query_jobs__filter_config_fun_succeeds(self, client: SystemClient):
        query = QueryJobsRequest(
            filter='config.fun.Contains("system.set_computer_desc")'
        )
        response = client.query_jobs(query=query)

        assert response is not None
        assert response.data is not None
        assert len(response.data) == response.count > 0

    def test__query_jobs__filter_config_fun_fails(self, client: SystemClient):
        query = QueryJobsRequest(
            filter='config.fun.Contains("system.set_computer_desc")'
        )
        with pytest.raises(ApiException):
            client.query_jobs(query=query)

    def test__query_jobs__filter_config_jid_succeeds(
        self, create_multiple_jobs, client: SystemClient
    ):
        query = QueryJobsRequest(filter=f"jid={create_multiple_jobs[0].jid}")
        response = client.query_jobs(query=query)

        assert response is not None
        assert response.data is not None
        assert len(response.data) == response.count == 1

    def test__query_jobs__filter_config_jid_fails(self, client: SystemClient):
        query = QueryJobsRequest(filter="jid=Invalid_jid")
        with pytest.raises(ApiException):
            client.query_jobs(query=query)

    def test__cancel_jobs__cancel_single_job_succeeds(self, client: SystemClient):
        arg = [["A description"]]
        tgt = [
            "HVM_domU--SN-ec200972-eeca-062e-5bf5-017a25451b39--MAC-0A-E1-20-D6-96-2B"
        ]
        fun = ["system.set_computer_desc"]
        metadata = {"queued": True, "refresh_minion_cache": {"grains": True}}
        job = CreateJobRequest(
            arg=arg,
            tgt=tgt,
            fun=fun,
            metadata=metadata,
        )
        response = client.create_job(job)

        cancel_job_request = CancelJobRequest(jid=response.jid, tgt=tgt[0])
        cancel_response = client.cancel_jobs([cancel_job_request])

        assert cancel_response.error is None

    def test__cancel_jobs__cancel_multiple_job_succeeds(self, client: SystemClient):
        arg_1 = [["A description"]]
        arg_2 = [["Another description"]]
        tgt = [
            "HVM_domU--SN-ec200972-eeca-062e-5bf5-017a25451b39--MAC-0A-E1-20-D6-96-2B"
        ]
        fun = ["system.set_computer_desc"]
        metadata = {"queued": True, "refresh_minion_cache": {"grains": True}}
        job_1 = CreateJobRequest(
            arg=arg_1,
            tgt=tgt,
            fun=fun,
            metadata=metadata,
        )
        response_1 = client.create_job(job_1)
        job_2 = CreateJobRequest(
            arg=arg_2,
            tgt=tgt,
            fun=fun,
            metadata=metadata,
        )
        response_2 = client.create_job(job_2)

        cancel_job_request_1 = CancelJobRequest(jid=response_1.jid, tgt=tgt[0])
        cancel_job_request_2 = CancelJobRequest(jid=response_2.jid, tgt=tgt[0])
        cancel_response = client.cancel_jobs(
            [cancel_job_request_1, cancel_job_request_2]
        )

        assert cancel_response.error is None

    def test__cancel_jobs__cancel_with_invalid_jid_fails(self, client: SystemClient):
        cancel_job_request = CancelJobRequest(jid="Invalid_jid", tgt="Invalid_tgt")
        cancel_response = client.cancel_jobs([cancel_job_request])

        assert cancel_response.error is not None
        assert cancel_response.error.message is not None
