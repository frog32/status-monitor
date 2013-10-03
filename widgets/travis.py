from widgets.base_widget import BaseWidget


class Widget(BaseWidget):
    name = 'travis'

    def __init__(self, *args, **kwargs):
        super(Widget, self).__init__(*args, **kwargs)
        self.repositorys = {}

    def register(self, aggregator_hub):
        aggregator = aggregator_hub.get('travis')
        aggregator.register_listener('repoUpdated', self.update_repo)

    def update_repo(self, repo_data):
        new_repo = {}
        for f in ("id", "slug", "last_build_state", "last_build_finished_at", "last_build_number", "last_build_duration"):
            new_repo[f] = repo_data[f]
        self.repositorys[repo_data["id"]] = new_repo
        self.message_broadcast("update", new_repo)

    def initialize(self, client):
        for repo in self.repositorys.values():
            self.message_to_client(client, 'update', repo)
