from widgets.base_widget import BaseWidget
from operator import itemgetter


class Widget(BaseWidget):
    name = 'travis'

    def __init__(self, *args, **kwargs):
        super(Widget, self).__init__(*args, **kwargs)
        self.repositorys = []

    def register(self, aggregator_hub):
        aggregator = aggregator_hub.get('travis')
        aggregator.register_listener('repoUpdated', self.update_repo)

    def update_repo(self, repo_data):
        new_repo = {}
        for f in ("id", "slug", "last_build_state", "last_build_finished_at", "last_build_number", "last_build_duration"):
            new_repo[f] = repo_data[f]
        for repo in self.repositorys:
            if repo["id"] == new_repo["id"]:
                self.repositorys.remove(repo)
        self.repositorys.append(new_repo)
        self.repositorys = sorted(self.repositorys, key=itemgetter('last_build_finished_at'), reverse=True)
        self.message_broadcast("update", self.repositorys)

    def initialize(self, client):
        self.message_to_client(client, 'update', self.repositorys)
