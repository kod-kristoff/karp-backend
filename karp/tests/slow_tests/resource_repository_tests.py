from karp.domain.models.resource import Resource
from karp.domain.commands import CreateResourceCommand
from karp.services import CreateResourceHandler
from karp.adapters.orm import SqlAlchemy

from expects import expect, equal, have_len


class When_we_load_a_persisted_resource:
    def given_a_database_containing_an_resource(self):

        self.db = SqlAlchemy("sqlite://")
        self.db.configure_mappings()
        self.db.recreate_schema()

        cmd = CreateResourceCommand(
            "fred", "fred@example.org", "forgot my password again"
        )
        handler = CreateResourceHandler(self.db.unit_of_work_manager)
        handler.handle(cmd)

    def because_we_load_the_resources(self):
        self.resources = self.db.get_session().query(Resource).all()

    def we_should_have_loaded_a_single_resource(self):
        expect(self.resources).to(have_len(1))

    def it_should_have_the_correct_description(self):
        expect(self.resources[0].description).to(equal("forgot my password again"))

    def it_should_have_the_correct_reporter_details(self):
        expect(self.resources[0].reporter.name).to(equal("fred"))

    def it_should_have_the_correct_reporter_details(self):
        expect(self.resources[0].reporter.email).to(equal("fred@example.org"))
