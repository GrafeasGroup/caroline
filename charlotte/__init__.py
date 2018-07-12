from charlotte.engine import Base

__version__ = "0.0.1"

__all__ = ["Prototype", "__version__"]


class Prototype(Base):
    def __init__(self, redis_conn):
        super().__init__(redis_conn)


if __name__ == "__main__":

    class User(Prototype):
        def __init__(self, username):
            super().__init__("redis")

    pam = User("pam")
    print(pam)
    pam.update("transcriptions", pam.get("transcriptions", 1) + 1)
    print(pam.get("transcriptions"))
    pam.save()