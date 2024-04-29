from torrentool.api import Torrent
from qbittorrent import Client
import pandas as pd
from sklearn.tree import DecisionTreeClassifier


def main():
    # sender:
    magnet_link = pack_to_torrent(src_path='src/path')
    # send magnet_link to receiver any way

    # receiver:
    get_from_magnet_link(magnet_link, dst_path='dst/path')

    df = pd.read_csv('dst/path/mnist_train.csv')
    classifier = DecisionTreeClassifier()
    classifier.fit(df)


def pack_to_torrent(src_path: str) -> str:
    my_torrent = create_torrent_file(
        src_path=src_path, torrent_file='my.torrent',
    )
    sender_client = qbittorrent_login(
        url='http:/localhost:8080/', username='admin1', password='admin1',
    )
    start_share_torrent(
        client=sender_client,
        torrent_file='my.torrent',
        src_path=src_path,
    )
    magnet_link = extract_magnet_link(torrent_file=my_torrent)
    sender_client.logout()
    return magnet_link


def get_from_magnet_link(magnet_link: str, dst_path: str):
    receiver_client = qbittorrent_login(
        url='http:/localhost:8080/', username='admin2', password='admin2',
    )
    get_files_from_magnet_link(
        client=receiver_client, magnet_link=magnet_link, dst_path=dst_path,
    )
    receiver_client.logout()


def create_torrent_file(src_path: str, torrent_file: str) -> Torrent:
    new_torrent = Torrent.create_from(src_path)
    new_torrent.to_file(torrent_file)
    return new_torrent


def qbittorrent_login(url: str, username: str, password: str) -> Client:
    qb = Client(url)
    qb.login(username=username, password=password)
    return qb


def start_share_torrent(client: Client, torrent_file: str, src_path: str):
    with open(torrent_file, 'rb') as file:
        client.download_from_file(file, savepath=src_path)


def extract_magnet_link(torrent_file: Torrent) -> str:
    return torrent_file.magnet_link


def get_files_from_magnet_link(
    client: Client, magnet_link: str, dst_path: str,
):
    client.download_from_link(magnet_link, savepath=dst_path)
