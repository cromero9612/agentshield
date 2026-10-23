from botocore.exceptions import ClientError, NoCredentialsError

from agent.bedrock_check import classify, probe, recommend, scan


def err(code, msg):
    return ClientError({"Error": {"Code": code, "Message": msg}}, "Converse")


def test_classification_of_the_errors_seen_on_a_new_account():
    assert classify(err("ThrottlingException", "Too many tokens per day, please wait"))[0] == "CUOTA"
    assert classify(err("AccessDeniedException", "Your account is currently being verified."))[0] == "VERIFICANDO"
    assert classify(err("AccessDeniedException", "anthropic.claude-sonnet-5-5 is not available for this account."))[0] == "NO_DISPONIBLE"
    assert classify(err("AccessDeniedException", "User is not authorized to perform bedrock:InvokeModel"))[0] == "SIN_PERMISO"
    assert classify(err("ValidationException", "Invocation of model ID with on-demand throughput isn't supported"))[0] == "NO_APLICA"
    assert classify(NoCredentialsError())[0] == "SIN_CREDENCIALES"


class FakeRuntime:
    """Modelos 'ok' responden; 'notools' responde pero rechaza herramientas; el resto falla con el error indicado."""

    def __init__(self, behaviour):
        self.behaviour = behaviour

    def converse(self, modelId, **kwargs):
        b = self.behaviour[modelId]
        if isinstance(b, Exception):
            raise b
        if b == "notools" and "toolConfig" in kwargs:
            raise err("ValidationException", "This model doesn't support tool use")
        return {"output": {}}


class FakeBedrock:
    def __init__(self, ids):
        self.ids = ids

    def list_inference_profiles(self, **kw):
        return {"inferenceProfileSummaries": [{"inferenceProfileId": i} for i in self.ids]}

    def list_foundation_models(self, **kw):
        return {"modelSummaries": []}


def test_probe_reports_ok_with_and_without_tool_support():
    rt = FakeRuntime({"a": "ok", "b": "notools"})
    assert probe(rt, "a") == {"model": "a", "status": "OK", "detail": "responde", "tools": True}
    assert probe(rt, "b")["tools"] is False


def test_scan_and_recommendation_prefers_a_working_model_with_tools():
    behaviour = {"us.amazon.nova-lite-v1:0": "ok", "global.anthropic.claude-sonnet-4-6": err("ThrottlingException", "Too many tokens per day"),
                 "us.meta.llama3": "notools"}

    def factory(service, region):
        return FakeBedrock(list(behaviour)) if service == "bedrock" else FakeRuntime(behaviour)

    results = scan(factory, ["us-east-1"], 10)
    statuses = {x["model"]: x["status"] for x in results["us-east-1"]}
    assert statuses["global.anthropic.claude-sonnet-4-6"] == "CUOTA" and statuses["us.amazon.nova-lite-v1:0"] == "OK"
    assert recommend(results) == ("us-east-1", "us.amazon.nova-lite-v1:0")


def test_no_recommendation_when_everything_fails():
    behaviour = {"m1": err("AccessDeniedException", "not available for this account")}
    results = scan(lambda s, r: FakeBedrock(["m1"]) if s == "bedrock" else FakeRuntime(behaviour), ["us-east-1"], 5)
    assert recommend(results) is None
