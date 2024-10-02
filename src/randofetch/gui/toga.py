import flet as ft
from randofetch.cli import BaseConfig, Fetcher, FetcherSet, init_fetcher_list

BASE_CONFIG = BaseConfig()


def main(page: ft.Page):
    images_in_config = BASE_CONFIG.image_list
    lv = ft.ListView(expand=True, spacing=10)
    col = ft.Column([])
    for impath in images_in_config:
        lv.controls.append(
            (ft.Image(str(impath), width=100, height=100, fit=ft.ImageFit("contain")))
        )
    t = ft.Tabs(
        selected_index=1,
        tabs=[ft.Tab(text="Images in Config Folder", content=ft.Container(content=lv))],
    )
    page.add(t)
    # page.add(ft.SafeArea(ft.Text("Hello, Flet!")))


ft.app(main)
