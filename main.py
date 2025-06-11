import pygame
import random
import os
import tkinter as tk
from tkinter import messagebox
import json
from datetime import datetime
import speech_recognition as sr
import pyttsx3
import threading

class Config:
    def __init__(self):
        self.TAMANHO_TELA = (1000, 700)
        self.COR_BRANCO = (255, 255, 255)  
        self.COR_PRETO = (0, 0, 0)
        self.COR_AMARELO_CLARO = (255, 255, 200)

        self.CAMINHOS_ASSETS = {
            "icone": "assets/icone.png",
            "jogador": "assets/jogador.png",
            "fundo_start": "assets/chopemenace2.jpg",
            "fundo_jogo": "assets/fundoNuvens.jpg",
            "fundo_dead": "assets/teladead2.jpg",
            "missel": "assets/chopp.png",
            "inimigo": "assets/inimigo.png",
            "lobao": "assets/lobao.png",
            "som_missel": "assets/laserBeam.mp3",
            "som_explosao": "assets/Chamber.mp3",
            "musica_fundo": "assets/fundomusica.mp3",
        }

        self.TAMANHOS_ENTIDADES = {
            "jogador": (190, 280),
            "missel": (120, 150),
            "inimigo": (200, 200),
            "lobao_base": (200, 200),
        }

        self.FONTES = {
            "menu": ("arialblack", 18),
            "morte": ("arial", 120),
            "pause": ("arialblack", 90),
            "placar_titulo": ("arialblack", 30),
            "placar_item": ("arialblack", 16),
            "botao_dead": ("archivot", 28),
            "botao_padrao": ("arialblack", 28)
        }

        self.LOBAO_ANIMACAO = {
            "min_scale": 0.95,
            "max_scale": 1.05,
            "speed": 0.0015,
        }

        self.VOZ_CONFIG = {
            "intervalo_reconhecimento": 1500,
            "timeout_escuta": 3,
            "phrase_time_limit": 3,
        }

configs = Config()

def inicializarBancoDeDados():
    if not os.path.exists("log.dat"):
        with open("log.dat", "w") as f:
            json.dump({}, f)

def escreverDados(nome, pontos):
    try:
        with open("log.dat", "r") as f:
            dados = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        dados = {}

    data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    if nome not in dados:
        dados[nome] = []
    dados[nome].append({"pontos": pontos, "data_hora": data_hora})

    with open("log.dat", "w") as f:
        json.dump(dados, f, indent=4)

def carregar_imagem(caminho, tamanho=None):
    img = pygame.image.load(caminho)
    if tamanho:
        img = pygame.transform.scale(img, tamanho)
    return img

def carregar_recursos():
    recursos = {}
    for nome, caminho in configs.CAMINHOS_ASSETS.items():
        if "som" in nome or "musica" in nome:
            recursos[nome] = pygame.mixer.Sound(caminho) if "som" in nome else caminho
        else:
            tamanho = configs.TAMANHOS_ENTIDADES.get(nome)
            recursos[nome] = carregar_imagem(caminho, tamanho)

    recursos["inimigo_scaled"] = carregar_imagem(configs.CAMINHOS_ASSETS["inimigo"], configs.TAMANHOS_ENTIDADES["inimigo"])

    recursos["fonte_menu"] = pygame.font.SysFont(*configs.FONTES["menu"])
    recursos["fonte_morte"] = pygame.font.SysFont(*configs.FONTES["morte"])
    recursos["fonte_pause"] = pygame.font.SysFont(*configs.FONTES["pause"])
    recursos["fonte_placar_titulo"] = pygame.font.SysFont(*configs.FONTES["placar_titulo"])
    recursos["fonte_placar_item"] = pygame.font.SysFont(*configs.FONTES["placar_item"])
    try:
        recursos["fonte_botao_dead"] = pygame.font.SysFont(*configs.FONTES["botao_dead"])
    except:
        recursos["fonte_botao_dead"] = pygame.font.SysFont("arialblack", 28)
    recursos["fonte_botao_padrao"] = pygame.font.SysFont(*configs.FONTES["botao_padrao"])
    return recursos

pygame.init()
inicializarBancoDeDados()
recursos = carregar_recursos()

tela = pygame.display.set_mode(configs.TAMANHO_TELA)
pygame.display.set_caption("Chope Menace") 
pygame.display.set_icon(recursos["icone"])

relogio = pygame.time.Clock()

pygame.mixer.music.load(recursos["musica_fundo"])

tts_engine = pyttsx3.init()
comando_voz_global = None
comando_lock = threading.Lock()

def falar(texto):
    tts_engine.say(texto)
    tts_engine.runAndWait()

def reconhecer_voz_thread(callback):
    r = sr.Recognizer()
    with sr.Microphone() as source:
        try:
            r.adjust_for_ambient_noise(source, duration=0.5)
            print("Aguardando comando de voz...")
            audio = r.listen(source, timeout=configs.VOZ_CONFIG["timeout_escuta"],
                             phrase_time_limit=configs.VOZ_CONFIG["phrase_time_limit"])
            texto = r.recognize_google(audio, language="pt-BR")
            print(f"Comando reconhecido: {texto.lower()}")
            callback(texto.lower())
        except sr.WaitTimeoutError:
            callback(None)
        except sr.UnknownValueError:
            callback(None)
        except sr.RequestError as e:
            print(f"Erro no serviço de reconhecimento de voz; {e}")
            callback(None)
        except Exception as e:
            print(f"Erro inesperado no reconhecimento de voz: {e}")
            callback(None)

def set_comando_global(comando):
    global comando_voz_global
    with comando_lock:
        comando_voz_global = comando

def desenhar_botao(superficie, rect, texto, fonte, cor_fundo, cor_texto):
    pygame.draw.rect(superficie, cor_fundo, rect, border_radius=20)
    texto_surface = fonte.render(texto, True, cor_texto)
    superficie.blit(texto_surface, texto_surface.get_rect(center=rect.center))

def obter_nome_jogador():
    largura_janela_tk = 300
    altura_janela_tk = 100
    nome_jogador = ""

    def submeter_nome():
        nonlocal nome_jogador
        nome_digitado = entry_nome.get().strip()
        if not nome_digitado:
            messagebox.showwarning("Aviso", "Por favor, digite seu nome!")
        else:
            nome_jogador = nome_digitado
            root.destroy()

    root = tk.Tk()
    largura_tela_monitor = root.winfo_screenwidth()
    altura_tela_monitor = root.winfo_screenheight()
    pos_x_tk = (largura_tela_monitor - largura_janela_tk) // 2
    pos_y_tk = (altura_tela_monitor - altura_janela_tk) // 2
    root.geometry(f"{largura_janela_tk}x{altura_janela_tk}+{pos_x_tk}+{pos_y_tk}")
    root.title("Informe seu nickname")
    root.protocol("WM_DELETE_WINDOW", lambda: None) 

    label_nome = tk.Label(root, text="Digite seu nome para começar:")
    label_nome.pack(pady=5)

    entry_nome = tk.Entry(root)
    entry_nome.pack(pady=5)
    entry_nome.focus_set()

    botao = tk.Button(root, text="Enviar", command=submeter_nome)
    botao.pack(pady=5)

    root.bind('<Return>', lambda event=None: botao.invoke())
    root.mainloop()

    return nome_jogador if nome_jogador else None

def tela_boas_vindas(nome_jogador):
    largura_botao = 200
    altura_botao = 50

    while True:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                quit()
            elif evento.type == pygame.MOUSEBUTTONUP:
                mouse_pos = pygame.mouse.get_pos()
                if start_button_rect.collidepoint(mouse_pos):
                    return

        tela.fill(configs.COR_BRANCO)
        tela.blit(recursos["fundo_jogo"], (0, 0))

        texto_bem_vindo = recursos["fonte_menu"].render(f"Olá, {nome_jogador}!", True, configs.COR_BRANCO)
        texto_instrucoes1 = recursos["fonte_menu"].render("Use as SETAS ESQUERDA e DIREITA para se mover.", True, configs.COR_BRANCO)
        texto_instrucoes2 = recursos["fonte_menu"].render("Desvie dos chopps envenenados do Evil Marcão.", True, configs.COR_BRANCO)
        texto_instrucoes3 = recursos["fonte_menu"].render("Pressione ESPAÇO ou diga 'pausar' para pausar/retomar o jogo.", True, configs.COR_BRANCO)

        centro_tela_x = configs.TAMANHO_TELA[0] / 2
        tela.blit(texto_bem_vindo, texto_bem_vindo.get_rect(center=(centro_tela_x, 250)))
        tela.blit(texto_instrucoes1, texto_instrucoes1.get_rect(center=(centro_tela_x, 300)))
        tela.blit(texto_instrucoes2, texto_instrucoes2.get_rect(center=(centro_tela_x, 330)))
        tela.blit(texto_instrucoes3, texto_instrucoes3.get_rect(center=(centro_tela_x, 360)))

        start_x = centro_tela_x - (largura_botao / 2)
        start_button_rect = pygame.Rect(start_x, 450, largura_botao, altura_botao)
        desenhar_botao(tela, start_button_rect, "Iniciar Partida", recursos["fonte_menu"], configs.COR_BRANCO, configs.COR_PRETO)

        pygame.display.update()
        relogio.tick(60)

def jogar():
    global comando_voz_global

    recursos["som_explosao"].stop() 

    nome = obter_nome_jogador()
    if nome is None:
        quit()

    tela_boas_vindas(nome)

    posicaoXPersona = 400
    posicaoYPersona = (configs.TAMANHO_TELA[1] / 2) - (recursos["jogador"].get_height() / 2) + 150
    movimentoXPersona = 0

    larguraPersona = recursos["jogador"].get_width()
    alturaPersona = recursos["jogador"].get_height()

    larguraInimigo = recursos["inimigo_scaled"].get_width()
    alturaInimigo = recursos["inimigo_scaled"].get_height()
    posicaoXInimigo = 0
    posicaoYInimigo = 10
    movimentoXInimigo = 5

    larguraMissel = recursos["missel"].get_width()
    alturaMissel = recursos["missel"].get_height()
    posicaoXMissel = posicaoXInimigo + (larguraInimigo / 2) - (larguraMissel / 2)
    posicaoYMissel = alturaInimigo
    velocidadeMissel = 1

    pontos = 0
    paused = False

    lobao_current_scale = configs.LOBAO_ANIMACAO["min_scale"]
    lobao_scaling_up = True

    recursos["som_missel"].play()
    pygame.mixer.music.play(-1)
    pygame.mixer.music.set_volume(1.0)

    ultima_tentativa_reconhecimento = pygame.time.get_ticks()

    while True:
        agora = pygame.time.get_ticks()
        if agora - ultima_tentativa_reconhecimento > configs.VOZ_CONFIG["intervalo_reconhecimento"]:
            ultima_tentativa_reconhecimento = agora
            voice_thread = threading.Thread(target=reconhecer_voz_thread, args=(set_comando_global,))
            voice_thread.daemon = True
            voice_thread.start()

        with comando_lock:
            comando = comando_voz_global
            comando_voz_global = None

        if comando:
            if "pausar" in comando:
                if not paused:
                    paused = True
                    pygame.mixer.music.set_volume(0.2)
                    falar("Jogo pausado.")
            elif "continuar" in comando or "retomar" in comando:
                if paused:
                    paused = False
                    pygame.mixer.music.set_volume(1.0)
                    falar("Jogo retomado.")

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                quit()

            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_SPACE:
                    paused = not paused
                    if paused:
                        pygame.mixer.music.set_volume(0.2)
                        falar("Jogo pausado.")
                    else:
                        pygame.mixer.music.set_volume(1.0)
                        falar("Jogo retomado.")

                if not paused:
                    if evento.key == pygame.K_RIGHT:
                        movimentoXPersona = 15
                    elif evento.key == pygame.K_LEFT:
                        movimentoXPersona = -15
            if evento.type == pygame.KEYUP:
                if not paused:
                    if evento.key == pygame.K_RIGHT or evento.key == pygame.K_LEFT:
                        movimentoXPersona = 0

        if not paused:
            posicaoXInimigo += movimentoXInimigo
            if posicaoXInimigo < 0 or posicaoXInimigo > configs.TAMANHO_TELA[0] - larguraInimigo:
                movimentoXInimigo = -movimentoXInimigo

            posicaoXPersona += movimentoXPersona
            posicaoXPersona = max(0, min(posicaoXPersona, configs.TAMANHO_TELA[0] - larguraPersona))

            posicaoYMissel += velocidadeMissel
            if posicaoYMissel > configs.TAMANHO_TELA[1]:
                posicaoYMissel = alturaInimigo
                pontos += 1
                velocidadeMissel += 0.5
                posicaoXMissel = posicaoXInimigo + (larguraInimigo / 2) - (larguraMissel / 2)
                recursos["som_missel"].play()

            persona_hitbox = pygame.Rect(posicaoXPersona + 50, posicaoYPersona + 40, larguraPersona - 100, alturaPersona - 60)
            missel_hitbox = pygame.Rect(posicaoXMissel + 45, posicaoYMissel + 50, larguraMissel - 90, alturaMissel - 85)

            if persona_hitbox.colliderect(missel_hitbox):
                escreverDados(nome, pontos)
                dead()

            if lobao_scaling_up:
                lobao_current_scale += configs.LOBAO_ANIMACAO["speed"]
                if lobao_current_scale >= configs.LOBAO_ANIMACAO["max_scale"]:
                    lobao_current_scale = configs.LOBAO_ANIMACAO["max_scale"]
                    lobao_scaling_up = False
            else:
                lobao_current_scale -= configs.LOBAO_ANIMACAO["speed"]
                if lobao_current_scale <= configs.LOBAO_ANIMACAO["min_scale"]:
                    lobao_current_scale = configs.LOBAO_ANIMACAO["min_scale"]
                    lobao_scaling_up = True

        tela.fill(configs.COR_BRANCO)
        tela.blit(recursos["fundo_jogo"], (0,0))
        tela.blit(recursos["jogador"], (posicaoXPersona, posicaoYPersona))
        tela.blit(recursos["missel"], (posicaoXMissel, posicaoYMissel))

        current_lobao_width = int(configs.TAMANHOS_ENTIDADES["lobao_base"][0] * lobao_current_scale)
        current_lobao_height = int(configs.TAMANHOS_ENTIDADES["lobao_base"][1] * lobao_current_scale)
        lobao_scaled = pygame.transform.scale(recursos["lobao"], (current_lobao_width, current_lobao_height))

        padding = 10
        lobao_pos_x = configs.TAMANHO_TELA[0] - lobao_scaled.get_width() - padding
        lobao_pos_y = padding
        tela.blit(lobao_scaled, (lobao_pos_x, lobao_pos_y))
        
        tela.blit(recursos["inimigo_scaled"], (posicaoXInimigo, posicaoYInimigo))

        texto_pontos = recursos["fonte_menu"].render("Pontos: "+str(pontos), True, configs.COR_BRANCO)
        tela.blit(texto_pontos, (15,15))

        texto_pause_msg = recursos["fonte_menu"].render("• Pressione Espaço ou diga 'pausar' para Pausar o Jogo", True, configs.COR_BRANCO)
        posicao_x_msg = 15 + texto_pontos.get_width() + 20
        tela.blit(texto_pause_msg, (posicao_x_msg, 15))

        if paused:
            overlay = pygame.Surface(configs.TAMANHO_TELA, pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            tela.blit(overlay, (0, 0))

            texto_pause = recursos["fonte_pause"].render("PAUSE", True, configs.COR_BRANCO)
            texto_rect = texto_pause.get_rect(center=(configs.TAMANHO_TELA[0]/2, configs.TAMANHO_TELA[1]/2))
            tela.blit(texto_pause, texto_rect)

        pygame.display.update()
        relogio.tick(60)

def start():
    largura_botao = 220
    altura_botao = 60

    while True:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                quit()
            elif evento.type == pygame.MOUSEBUTTONUP:
                mouse_pos = pygame.mouse.get_pos()
                if start_button_rect.collidepoint(mouse_pos):
                    jogar()
                if quit_button_rect.collidepoint(mouse_pos):
                    quit()

        tela.fill(configs.COR_BRANCO)
        tela.blit(recursos["fundo_start"], (0, 0))

        centro_x = (configs.TAMANHO_TELA[0] - largura_botao) // 2
        start_y = (configs.TAMANHO_TELA[1] // 2) - 80
        quit_y = start_y + 100

        start_button_rect = pygame.Rect(centro_x, start_y, largura_botao, altura_botao)
        desenhar_botao(tela, start_button_rect, "Iniciar Game", recursos["fonte_botao_padrao"], configs.COR_BRANCO, configs.COR_PRETO)

        quit_button_rect = pygame.Rect(centro_x, quit_y, largura_botao, altura_botao)
        desenhar_botao(tela, quit_button_rect, "Sair do Game", recursos["fonte_botao_padrao"], configs.COR_BRANCO, configs.COR_PRETO)

        pygame.display.update()
        relogio.tick(60)

def dead():
    pygame.mixer.music.stop()
    recursos["som_explosao"].set_volume(1.0)
    recursos["som_explosao"].play()

    log_partidas_raw = []
    try:
        with open("log.dat", "r") as f:
            dados = json.load(f)
            for nickname, partidas_do_jogador in dados.items():
                if isinstance(partidas_do_jogador, list):
                    for partida in partidas_do_jogador:
                        if isinstance(partida, dict) and "pontos" in partida and "data_hora" in partida:
                            log_partidas_raw.append({
                                "nickname": nickname,
                                "pontos": partida["pontos"],
                                "data_hora": partida["data_hora"]
                            })
                        else:
                            print(f"Aviso: Item de partida inesperado para {nickname}: {partida}")
                else:
                    if isinstance(partidas_do_jogador, list) and len(partidas_do_jogador) == 2 and isinstance(partidas_do_jogador[0], int) and isinstance(partidas_do_jogador[1], str):
                             log_partidas_raw.append({
                                 "nickname": nickname,
                                 "pontos": partidas_do_jogador[0],
                                 "data_hora": partidas_do_jogador[1]
                               })
                    else:
                        print(f"Aviso: Formato de log inesperado para {nickname}: {partidas_do_jogador}")
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    log_partidas_sorted = sorted(log_partidas_raw, key=lambda x: x["pontos"], reverse=True)
    ultimas_5_partidas = log_partidas_sorted[:5]

    while True:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                quit()
            elif evento.type == pygame.MOUSEBUTTONUP:
                mouse_pos = pygame.mouse.get_pos()
                if start_button_rect.collidepoint(mouse_pos):
                    jogar()
                if quit_button_rect.collidepoint(mouse_pos):
                    quit()

        tela.fill(configs.COR_BRANCO)
        tela.blit(recursos["fundo_dead"], (0,0))

        largura_botao = 200
        altura_botao = 50

        centro_x = (configs.TAMANHO_TELA[0] - largura_botao) // 2
        start_y = (configs.TAMANHO_TELA[1] // 2) + 150
        quit_y = start_y + 70

        start_button_rect = pygame.Rect(centro_x, start_y, largura_botao, altura_botao)
        desenhar_botao(tela, start_button_rect, "Jogar Novamente", recursos["fonte_botao_dead"], configs.COR_BRANCO, configs.COR_PRETO)

        quit_button_rect = pygame.Rect(centro_x, quit_y, largura_botao, altura_botao)
        desenhar_botao(tela, quit_button_rect, "Sair do Game", recursos["fonte_botao_dead"], configs.COR_BRANCO, configs.COR_PRETO)

        placar_bg_width = 250
        placar_bg_height = 130
        padding_right = 10
        padding_bottom = 10

        placar_bg_x = configs.TAMANHO_TELA[0] - placar_bg_width - padding_right
        placar_bg_y = configs.TAMANHO_TELA[1] - placar_bg_height - padding_bottom

        pygame.draw.rect(tela, configs.COR_BRANCO, (placar_bg_x, placar_bg_y, placar_bg_width, placar_bg_height), border_radius=3)
        pygame.draw.rect(tela, configs.COR_PRETO, (placar_bg_x, placar_bg_y, placar_bg_width, placar_bg_height), 2, border_radius=3)

        item_y_offset = 0
        item_start_y_inside_box = placar_bg_y + 8

        for i, record in enumerate(ultimas_5_partidas):
            item_text = f"{i+1}. {record['nickname']:<10} - {record['pontos']:>5}"
            item_surface = recursos["fonte_placar_item"].render(item_text, True, configs.COR_PRETO)
            item_rect = item_surface.get_rect(center=(placar_bg_x + placar_bg_width // 2, item_start_y_inside_box + item_y_offset))

            tela.blit(item_surface, item_rect)
            item_y_offset += 22

        if not ultimas_5_partidas:
            no_data_text = recursos["fonte_placar_item"].render("Nenhuma pontuação registrada.", True, configs.COR_PRETO)
            no_data_rect = no_data_text.get_rect(center=(placar_bg_x + placar_bg_width // 2, placar_bg_y + placar_bg_height // 2))
            tela.blit(no_data_text, no_data_rect)

        pygame.display.update()
        relogio.tick(60)

if __name__ == '__main__':
    start()