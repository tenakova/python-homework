import uuid
import datetime
import math


class UserDoesNotExistError(Exception):
    pass


class UserAlreadyExistsError(Exception):
    pass


class UsersNotConnectedError(Exception):
    pass


class User:
    def __init__(self, full_name):
        self.full_name = full_name
        self.uuid = uuid.uuid4()
        self.posts = []
        self.following = []

    def add_post(self, post_content):
        new_post = Post(self, post_content)
        self.posts.append(new_post)
        if len(self.posts) > 50:
            del self.posts[0]

    def get_post(self):
        for i in range(len(self.posts)):
            yield self.posts[i]


class Post:
    def __init__(self, author, content):
        self.author = author.uuid
        self.published_at = datetime.datetime.now()
        self.content = content


def user_exists(func):
    def checked(self, *args):
        for arg in args:
            if arg not in self.graph.keys():
                raise UserDoesNotExistError
        return func(self, *args)
    return checked


class SocialGraph:
    def __init__(self):
        self.graph = {}

    def add_user(self, user):
        if user.uuid in self.graph.keys():
            raise UserAlreadyExistsError
        else:
            self.graph[user.uuid] = user

    @user_exists
    def get_user(self, user_uuid):
        return self.graph[user_uuid]

    @user_exists
    def delete_user(self, user_uuid):
        self.graph[user_uuid].following = []
        for uuid, user in self.graph.items():
            if user_uuid in user.following:
                user.following.remove(user_uuid)
        del self.graph[user_uuid]

    @user_exists
    def follow(self, follower, followee):
        if followee not in self.graph[follower].following:
            self.graph[follower].following.append(followee)

    @user_exists
    def unfollow(self, follower, followee):
        if followee in self.graph[follower].following:
            self.graph[follower].following.remove(followee)

    @user_exists
    def is_following(self, follower, followee):
        return followee in self.graph[follower].following

    @user_exists
    def followers(self, user_uuid):
        followers = set()
        for uuid, user in self.graph.items():
            if user_uuid in user.following:
                followers.add(uuid)

        return followers

    @user_exists
    def following(self, user_uuid):
        return set(self.graph[user_uuid].following)

    @user_exists
    def friends(self, user_uuid):
        friends = set()
        for followee in self.graph[user_uuid].following:
            if self.is_following(followee, user_uuid):
                friends.add(followee)

        return friends

    @user_exists
    def min_distance(self, from_user_uuid, to_user_uuid):
        if from_user_uuid == to_user_uuid:
            return 0
        level = 1
        queue = self.graph[from_user_uuid].following
        next_level = []
        visited = [from_user_uuid]
        while queue:
            for followed in queue:
                if followed == to_user_uuid:
                    return level
                else:
                    for next_level_followed in self.graph[followed].following:
                        if next_level_followed not in visited:
                            next_level.append(next_level_followed)
                    visited.append(followed)
            level += 1
            queue = next_level
            next_level = []
        raise UsersNotConnectedError

    @user_exists
    def max_distance(self, user_uuid):
        if not self.graph[user_uuid].following:
            return math.inf
        queue = [user_uuid]
        visited = [user_uuid]
        next_level = []
        max_distance = -1
        while queue:
            for user in queue:
                for followed in self.graph[user].following:
                    if followed not in visited:
                        next_level.append(followed)
                        visited.append(followed)
            max_distance += 1
            queue = next_level
            next_level = []
        return max_distance

    def nth_layer_followings(self, user_uuid, n):
        if user_uuid not in self.graph.keys():
            raise UserDoesNotExistError
        queue = []
        next_level = self.graph[user_uuid].following
        visited = [user_uuid]
        for i in range(n):
            queue = next_level
            next_level = []
            for followed in queue:
                for next_level_followed in self.graph[followed].following:
                    if next_level_followed not in visited:
                        next_level.append(next_level_followed)
                visited.append(followed)
        return set(queue)

    def generate_feed(self, user_uuid, offset=0, limit=10):
        if user_uuid not in self.graph.keys():
            raise UserDoesNotExistError
        feed = []
        for user in self.graph[user_uuid].following:
            feed.extend(self.graph[user].posts)
        feed.sort(key=lambda posts: posts.published_at, reverse=True)
        if len(feed) < (limit - offset):
            return feed[offset::]
        else:
            return feed[offset:(limit + offset)]
        