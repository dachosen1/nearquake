from nearquake.cli import parse_arguments
from nearquake.cli.command_handlers import (BackfillCommandHandler,
                                            CommandHandlerFactory,
                                            DailyCommandHandler,
                                            FunFactCommandHandler,
                                            InitializeCommandHandler,
                                            LiveCommandHandler,
                                            MonthlyCommandHandler,
                                            WeeklyCommandHandler)
from nearquake.config import POSTGRES_CONNECTION_URL
from nearquake.utils.db_sessions import DbSessionManager


def main():
    """Execute the application based on command-line arguments."""
    args = parse_arguments()
    factory = CommandHandlerFactory()

    # Register command handlers
    factory.register("live", LiveCommandHandler)
    factory.register("daily", DailyCommandHandler)
    factory.register("weekly", WeeklyCommandHandler)
    factory.register("monthly", MonthlyCommandHandler)
    factory.register("fun", FunFactCommandHandler)
    factory.register("backfill", BackfillCommandHandler)
    factory.register("initialize", InitializeCommandHandler)

    # Create DB session manager
    db_session = DbSessionManager(url=POSTGRES_CONNECTION_URL)

    with db_session:
        for command_name, enabled in vars(args).items():
            if enabled:
                handler = factory.create(command_name)
                if handler:
                    handler.execute(db_session)


if __name__ == "__main__":
    main()
