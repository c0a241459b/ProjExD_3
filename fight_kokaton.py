import math
import os
import random
import sys
import time
import pygame as pg


WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
NUM_OF_BOMBS = 5  # 爆弾の数


os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


class Bird:
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -5),
        pg.K_DOWN: (0, +5),
        pg.K_LEFT: (-5, 0),
        pg.K_RIGHT: (+5, 0),
    }
    img0 = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)
    img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん（右向き）
    imgs = {  # 0度から反時計回りに定義
        (+5, 0): img,  # 右
        (+5, -5): pg.transform.rotozoom(img, 45, 0.9),  # 右上
        (0, -5): pg.transform.rotozoom(img, 90, 0.9),  # 上
        (-5, -5): pg.transform.rotozoom(img0, -45, 0.9),  # 左上
        (-5, 0): img0,  # 左
        (-5, +5): pg.transform.rotozoom(img0, 45, 0.9),  # 左下
        (0, +5): pg.transform.rotozoom(img, -90, 0.9),  # 下
        (+5, +5): pg.transform.rotozoom(img, -45, 0.9),  # 右下
    }

    def __init__(self, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数 xy：こうかとん画像の初期位置座標タプル
        """
        self.img = __class__.imgs[(+5, 0)]
        self.rct: pg.Rect = self.img.get_rect()
        self.rct.center = xy
        self.dire = (+5, 0)  # こうかとんの向きを表すタプル

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.img = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.img, self.rct)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rct.move_ip(sum_mv)
        if check_bound(self.rct) != (True, True):
            self.rct.move_ip(-sum_mv[0], -sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.img = __class__.imgs[tuple(sum_mv)]
            self.dire = tuple(sum_mv)  # 合計移動量でdireを更新
        screen.blit(self.img, self.rct)


class Beam:
    """
    こうかとんが放つビームに関するクラス
    """
    def __init__(self, bird: "Bird"):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん（Birdインスタンス）
        """
        # こうかとんが向いている方向を取得
        self.vx, self.vy = bird.dire
        
        # 角度を計算（直交座標から極座標へ変換）
        angle = math.degrees(math.atan2(-self.vy, self.vx))
        
        # ビーム画像を読み込んで回転
        self.img = pg.transform.rotozoom(pg.image.load("fig/beam.png"), angle, 1.0)
        self.rct = self.img.get_rect()
        
        # こうかとんのrctのwidthとheightおよび向いている方向を考慮した初期配置
        # ビームの中心横座標 = こうかとんの中心横座標 + こうかとんの横幅 * ビームの横速度 / 5
        self.rct.centerx = bird.rct.centerx + bird.rct.width * self.vx // 5
        # ビームの中心縦座標 = こうかとんの中心縦座標 + こうかとんの高さ * ビームの縦速度 / 5
        self.rct.centery = bird.rct.centery + bird.rct.height * self.vy // 5

    def update(self, screen: pg.Surface):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        if check_bound(self.rct) == (True, True):
            self.rct.move_ip(self.vx, self.vy)
            screen.blit(self.img, self.rct)


class Bomb:
    """
    爆弾に関するクラス
    """
    def __init__(self, color: tuple[int, int, int], rad: int):
        """
        引数に基づき爆弾円Surfaceを生成する
        引数1 color：爆弾円の色タプル
        引数2 rad：爆弾円の半径
        """
        self.img = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.img, color, (rad, rad), rad)
        self.img.set_colorkey((0, 0, 0))
        self.rct = self.img.get_rect()
        self.rct.center = random.randint(0, WIDTH), random.randint(0, HEIGHT)
        self.vx, self.vy = +5, +5

    def update(self, screen: pg.Surface):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        yoko, tate = check_bound(self.rct)
        if not yoko:
            self.vx *= -1
        if not tate:
            self.vy *= -1
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)


class Explosion:
    """
    爆発エフェクトに関するクラス
    """
    def __init__(self, bomb: "Bomb"):
        """
        爆発エフェクトSurfaceを生成する
        引数 bomb：爆発する爆弾（Bombインスタンス）
        """
        # 元の爆発画像を読み込む
        img = pg.image.load("fig/explosion.gif")
        # 元の画像と上下左右にflipした画像の2つをリストに格納
        self.imgs = [
            img,  # 元の画像
            pg.transform.flip(img, True, True)  # 上下左右反転
        ]
        self.rct = self.imgs[0].get_rect()
        self.rct.center = bomb.rct.center  # 爆発した爆弾の中心座標
        self.life = 20  # 表示時間（爆発時間）

    def update(self, screen: pg.Surface):
        """
        爆発エフェクトを描画する
        引数 screen：画面Surface
        """
        self.life -= 1  # 爆発経過時間を1減算
        if self.life > 0:
            # 爆発経過時間が正なら、Surfaceリストを交互に切り替えて爆発を演出
            img_index = (20 - self.life) // 2 % 2  # 2フレームごとに画像を切り替え
            screen.blit(self.imgs[img_index], self.rct)


class Score:
    """
    スコア管理用クラス
    """
    def __init__(self):
        # フォント設定（創英角ポップ体、サイズ30）
        self.fonto = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 30)
        # 文字色（青）
        self.color = (0, 0, 255)
        # スコア初期値
        self.value = 0
        # 初期文字列Surface生成
        self.img = self.fonto.render("スコア：0", False, self.color)
        # 文字列の中心座標（画面左下：横100, 縦HEIGHT-50）
        self.rct = self.img.get_rect()
        self.rct.center = (100, HEIGHT-50)

    def update(self, screen: pg.Surface):
        """
        現在のスコアを表示する文字列Surfaceを生成してスクリーンにblit
        """
        self.img = self.fonto.render(f"スコア：{self.value}", False, self.color)
        screen.blit(self.img, self.rct)


def main():
    pg.display.set_caption("たたかえ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load("fig/pg_bg.jpg")
    bird = Bird((300, 200))
    bombs = [Bomb((255, 0, 0), 10) for i in range(NUM_OF_BOMBS)]
    beams = []
    explosions = []  # Explosionインスタンス用の空リスト
    
    score = Score()  # 撃ち落とした爆弾の数
    clock = pg.time.Clock()
    tmr = 0
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                # スペースキー押下でBeamクラスのインスタンス生成
                beams.append(Beam(bird))

        screen.blit(bg_img, [0, 0])
        
        # 鳥と爆弾の衝突判定
        for bomb in bombs:
            if bird.rct.colliderect(bomb.rct):
                # ゲームオーバー時に，こうかとん画像を切り替え，1秒間表示させる
                bird.change_img(8, screen)
                pg.display.update()
                time.sleep(1)
                return

        # ビームと爆弾の衝突判定
        for beam in beams[:]:
            for bomb in bombs[:]:
                if beam.rct.colliderect(bomb.rct):
                    # 爆発エフェクトを生成
                    explosions.append(Explosion(bomb))
                    if bomb in bombs:
                        bombs.remove(bomb)  # 爆弾削除
                    if beam in beams:
                        beams.remove(beam)  # ビーム削除
                    score.value += 1  # スコア加算
                    bird.change_img(6, screen)
                    break

        # 画面外のビームを削除
        beams = [beam for beam in beams if check_bound(beam.rct) == (True, True)]

        # lifeが0より大きいExplosionインスタンスだけのリストにする
        explosions = [exp for exp in explosions if exp.life > 0]

        # キー入力と描画
        key_lst = pg.key.get_pressed()
        bird.update(key_lst, screen)

        # すべてのビームを更新
        for beam in beams:
            beam.update(screen)

        # すべての爆弾を更新
        for bomb in bombs:
            bomb.update(screen)
        
        # すべての爆発エフェクトを更新
        for explosion in explosions:
            explosion.update(screen)
        
        # スコア表示
        score.update(screen)
            
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()