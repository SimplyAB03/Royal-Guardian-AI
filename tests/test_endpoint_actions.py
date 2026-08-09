from endpoint.actions import ACTIONS, execute_action


def test_unknown_action_is_denied():
    result = execute_action("shell.anything", {"command": "whoami"})
    assert result["ok"] is False
    assert "allowlisted" in result["error"]


def test_no_arbitrary_shell_action_registered():
    ids = set(ACTIONS)
    assert "shell.execute" not in ids
    assert "powershell.execute" not in ids
    assert "cmd.execute" not in ids
