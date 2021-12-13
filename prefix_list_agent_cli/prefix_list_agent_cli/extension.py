import CliExtension


class ShowPrefixListAgent(CliExtension.ShowCommandClass):
    def handler(self, ctx):
        return {"enabled": False}

    def render(self, data):
        print("prefix-list-agent enabled: {}".format(data["enabled"]))


def Plugin(ctx):
    CliExtension.registerCommand("show_prefix_list_agent", ShowPrefixListAgent)
