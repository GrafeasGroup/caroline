from charlotte.engine import Base

__all__ = ["Prototype"]

Prototype = Base

if __name__ == "__main__":

    class User(Prototype):
        schema = {}
        default_structure = {}
        redis_obj = 'asdf'
        
    pam = User()

    pam = User("pam")
    print(pam)
    pam.update("transcriptions", pam.get("transcriptions", 1) + 1)
    print(pam.get("transcriptions"))
    pam.save()
