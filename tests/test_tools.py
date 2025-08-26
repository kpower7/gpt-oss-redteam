from gpt_oss_redteam.tools import get_fake_tools


def test_get_fake_tools_default_schema():
    tools = get_fake_tools()
    assert isinstance(tools, list) and len(tools) > 0

    t = tools[0]
    assert t.get("type") == "function"
    fn = t.get("function")
    assert isinstance(fn, dict)
    assert isinstance(fn.get("name"), str) and fn["name"]

    params = fn.get("parameters")
    assert isinstance(params, dict)
    assert params.get("type") == "object"

    props = params.get("properties")
    assert isinstance(props, dict) and "input" in props
    assert props["input"]["type"] == "string"
    assert "put all information here" in props["input"]["description"]

    required = params.get("required")
    assert required == ["input"]
    assert params.get("additionalProperties") is False


def test_get_fake_tools_custom_names():
    names = ["a.b", "x.y.z"]
    tools = get_fake_tools(names)
    assert [t["function"]["name"] for t in tools] == names
