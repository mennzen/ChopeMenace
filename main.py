import pygame
import random
import os
import tkinter as tk
from tkinter import messagebox
import json
from datetime import datetime

# --- Funções que estavam no arquivo 'recursos/funcoes.py' ---
def inicializarBancoDeDados():
    """Verifica se o arquivo de banco de dados existe, se não, cria um."""
    if not os.path.exists("base.atitus"):
        with open("base.atitus", "w") as f:
            json.dump({}, f)

def escreverDados(nome, pontos):
    """Escreve os dados da partida no arquivo JSON."""
    try:
        with open("base.atitus", "r") as f:
            dados = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        dados = {}

    data_hora = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    # Salva a pontuação do jogador com data e hora
    dados[nome] = [pontos, data_hora]

    with open("base.atitus", "w") as f:
        json.dump(dados, f, indent=4)
# --- Fim das funções auxiliares ---


pygame.init()
inicializarBancoDeDados()
tamanho = (1000,700)
relogio = pygame.time.Clock()
tela = pygame.display.set_mode( tamanho ) 
pygame.display.set_caption("Marcao X Pitt")
icone = pygame.image.load("assets/icone.png")
pygame.display.set_icon(icone)
branco = (255,255,255)
preto = (0, 0 ,0 )

# --- ALTERAÇÃO AQUI: Carrega e redimensiona a imagem do jogador ---
jogador_original = pygame.image.load("assets/jogador.png")
jogador = pygame.transform.scale(jogador_original, (190, 280)) # <-- REDIMENSIONADO AQUI (125x64 pixels)

fundoStart = pygame.image.load("assets/fundoinicial.png")
fundoJogo = pygame.image.load("assets/fundoJogo.png")
fundoDead = pygame.image.load("assets/fundoDead.png")
missel = pygame.transform.scale(pygame.image.load("assets/chopp.png"), (120, 150))
inimigo = pygame.image.load("assets/inimigo.png")
missileSound = pygame.mixer.Sound("assets/missile.wav")
explosaoSound = pygame.mixer.Sound("assets/explosao.wav")
fonteMenu = pygame.font.SysFont("arialblack",18)
fonteMorte = pygame.font.SysFont("arial",120)
fontePause = pygame.font.SysFont("arialblack", 90)
pygame.mixer.music.load("assets/fundomusica.mp3")

def jogar():
    largura_janela = 300
    altura_janela = 100 
    def obter_nome():
        global nome
        nome = entry_nome.get()
        if not nome:
            messagebox.showwarning("Aviso", "Por favor, digite seu nome!")
        else:
            root.destroy()

    root = tk.Tk()
    largura_tela = root.winfo_screenwidth()
    altura_tela = root.winfo_screenheight()
    pos_x = (largura_tela - largura_janela) // 2
    pos_y = (altura_tela - altura_janela) // 2
    root.geometry(f"{largura_janela}x{altura_janela}+{pos_x}+{pos_y}")
    root.title("Informe seu nickname")
    root.protocol("WM_DELETE_WINDOW", lambda: None) 

    label_nome = tk.Label(root, text="Digite seu nome para começar:")
    label_nome.pack(pady=5)

    entry_nome = tk.Entry(root)
    entry_nome.pack(pady=5)
    
    entry_nome.focus_set()

    botao = tk.Button(root, text="Enviar", command=obter_nome)
    botao.pack(pady=5)
    
    root.bind('<Return>', lambda event=None: botao.invoke())

    root.mainloop()
    
    try:
        nome
    except NameError:
        quit()
        
    tela_boas_vindas(nome)

    # --- Variáveis do Jogador ---
    posicaoXPersona = 400
    posicaoYPersona = 300
    movimentoXPersona  = 0
    movimentoYPersona  = 0
    # --- ALTERAÇÃO AQUI: Tamanho do jogador agora é pego da imagem redimensionada ---
    larguraPersona = jogador.get_width()
    alturaPersona = jogador.get_height()
    
    # --- VARIÁVEIS DO INIMIGO ---
    inimigo_img = pygame.transform.scale(inimigo, (200, 100))
    larguraInimigo = inimigo_img.get_width()
    alturaInimigo = inimigo_img.get_height()
    posicaoXInimigo = 0
    posicaoYInimigo = 10
    movimentoXInimigo = 5
    
    # --- Variáveis do Míssil ---
    larguaMissel  = 120
    alturaMissel  = 150
    posicaoXMissel = posicaoXInimigo + (larguraInimigo / 2) - (larguaMissel / 2)
    posicaoYMissel = alturaInimigo
    velocidadeMissel = 1
    
    # --- Variáveis do Jogo ---
    pontos = 0
    paused = False
    
    pygame.mixer.Sound.play(missileSound)
    pygame.mixer.music.play(-1)
    pygame.mixer.music.set_volume(1.0)

    while True:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                quit()
            
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_SPACE:
                    paused = not paused
                    if paused:
                        pygame.mixer.music.set_volume(0.2)
                    else:
                        pygame.mixer.music.set_volume(1.0)

            if not paused:
                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_RIGHT:
                        movimentoXPersona = 15
                    elif evento.key == pygame.K_LEFT:
                        movimentoXPersona = -15
                    elif evento.key == pygame.K_UP:
                        movimentoYPersona = -15
                    elif evento.key == pygame.K_DOWN:
                        movimentoYPersona = 15
                if evento.type == pygame.KEYUP:
                    if evento.key == pygame.K_RIGHT or evento.key == pygame.K_LEFT:
                        movimentoXPersona = 0
                    if evento.key == pygame.K_UP or evento.key == pygame.K_DOWN:
                        movimentoYPersona = 0
        
        if not paused:
            # Movimento do Inimigo
            posicaoXInimigo += movimentoXInimigo
            if posicaoXInimigo < 0 or posicaoXInimigo > tamanho[0] - larguraInimigo:
                movimentoXInimigo = -movimentoXInimigo

            # Movimento do jogador
            posicaoXPersona += movimentoXPersona      
            posicaoYPersona += movimentoYPersona      
            
            # Limites de tela para o jogador
            if posicaoXPersona < 0:
                posicaoXPersona = 0
            elif posicaoXPersona > tamanho[0] - larguraPersona:
                posicaoXPersona = tamanho[0] - larguraPersona
            if posicaoYPersona < 0:
                posicaoYPersona = 0
            elif posicaoYPersona > tamanho[1] - alturaPersona:
                posicaoYPersona = tamanho[1] - alturaPersona
            
            # Movimento do míssil
            posicaoYMissel += velocidadeMissel
            if posicaoYMissel > tamanho[1]:
                posicaoYMissel = alturaInimigo
                pontos += 1
                velocidadeMissel += 0.5 
                posicaoXMissel = posicaoXInimigo + (larguraInimigo / 2) - (larguaMissel / 2)
                pygame.mixer.Sound.play(missileSound)
            
            # Colisão
            # --- AJUSTE NA HITBOX: Usando as novas dimensões do jogador ---
            persona_hitbox = pygame.Rect(posicaoXPersona + 50, posicaoYPersona + 40, larguraPersona - 100, alturaPersona - 60)
            missel_hitbox = pygame.Rect(posicaoXMissel + 45, posicaoYMissel + 50, larguaMissel - 90, alturaMissel - 100)

            if persona_hitbox.colliderect(missel_hitbox):
                escreverDados(nome, pontos)
                dead()
        
        # --- PARTE DE DESENHO ---
        tela.fill(branco)
        tela.blit(fundoJogo, (0,0))
        tela.blit(inimigo_img, (posicaoXInimigo, posicaoYInimigo))
        tela.blit(jogador, (posicaoXPersona, posicaoYPersona)) # <-- ALTERAÇÃO AQUI: Usa a variável 'jogador'
        tela.blit(missel, (posicaoXMissel, posicaoYMissel))
        
        texto = fonteMenu.render("Pontos: "+str(pontos), True, branco)
        tela.blit(texto, (15,15))

        # Para depuração: desenhe as hitboxes (DESCOMENTE PARA VISUALIZAR)
        # pygame.draw.rect(tela, (255, 0, 0), persona_hitbox, 2) # Vermelho para o jogador
        # pygame.draw.rect(tela, (0, 0, 255), missel_hitbox, 2)  # Azul para o míssil

        # Tela de Pause
        if paused:
            overlay = pygame.Surface(tamanho, pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150)) 
            tela.blit(overlay, (0, 0))

            texto_pause = fontePause.render("PAUSE", True, branco)
            texto_rect = texto_pause.get_rect(center=(tamanho[0]/2, tamanho[1]/2))
            tela.blit(texto_pause, texto_rect)

        pygame.display.update()
        relogio.tick(60)

# O restante do código (start, dead, tela_boas_vindas) permanece igual
def start():
    larguraButtonStart = 220 
    alturaButtonStart  = 60
    larguraButtonQuit = 220 
    alturaButtonQuit  = 60

    fonteBotao = pygame.font.SysFont("arialblack", 28)

    while True:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                quit()
            elif evento.type == pygame.MOUSEBUTTONUP:
                mouse_pos = pygame.mouse.get_pos()
                if startButton.collidepoint(mouse_pos):
                    jogar()
                if quitButton.collidepoint(mouse_pos):
                    quit()

        tela.fill(branco)
        tela.blit(fundoStart, (0, 0))

        centro_x = (tamanho[0] - larguraButtonStart) // 2
        start_y = (tamanho[1] // 2) - 80
        quit_y = start_y + 100 

        startButton = pygame.draw.rect(tela, branco, (centro_x, start_y, larguraButtonStart, alturaButtonStart), border_radius=20)
        textoStart = fonteBotao.render("Iniciar Game", True, preto)
        tela.blit(textoStart, textoStart.get_rect(center=startButton.center))

        quitButton = pygame.draw.rect(tela, branco, (centro_x, quit_y, larguraButtonQuit, alturaButtonQuit), border_radius=20)
        textoQuit = fonteBotao.render("Sair do Game", True, preto)
        tela.blit(textoQuit, textoQuit.get_rect(center=quitButton.center))

        pygame.display.update()
        relogio.tick(60)

def dead():
    pygame.mixer.music.stop()
    pygame.mixer.Sound.play(explosaoSound)
    
    def mostrar_placar():
        root = tk.Tk()
        root.title("Log das Partidas")
        
        largura_janela_placar = 400
        altura_janela_placar = 300
        largura_tela = root.winfo_screenwidth()
        altura_tela = root.winfo_screenheight()
        pos_x = (largura_tela - largura_janela_placar) // 2
        pos_y = (altura_tela - altura_janela_placar) // 2
        root.geometry(f"{largura_janela_placar}x{altura_janela_placar}+{pos_x}+{pos_y}")


        label = tk.Label(root, text="Histórico de Pontuações", font=("Arial", 16))
        label.pack(pady=10)

        listbox = tk.Listbox(root, width=50, height=10, font=("Courier", 10))
        listbox.pack(pady=10, padx=10, fill="both", expand=True)
        
        try:
            with open("base.atitus", "r") as f:
                log_partidas = json.load(f)
            
            sorted_log = sorted(log_partidas.items(), key=lambda item: item[1][0], reverse=True)
            
            for nickname, (pontos, data) in sorted_log:
                texto_linha = f"{nickname:<15} | {pontos:>5} pts | {data}"
                listbox.insert(tk.END, texto_linha)
        except (FileNotFoundError, json.JSONDecodeError):
            listbox.insert(tk.END, "Nenhuma pontuação registrada ainda.")

        root.mainloop()

    mostrar_placar() 

    while True:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                quit()
            elif evento.type == pygame.MOUSEBUTTONUP:
                mouse_pos = pygame.mouse.get_pos()
                if startButton.collidepoint(mouse_pos):
                    jogar() 
                if quitButton.collidepoint(mouse_pos):
                    quit()

        tela.fill(branco)
        tela.blit(fundoDead, (0,0))
        
        larguraButton = 200
        alturaButton = 50
        centro_x = (tamanho[0] - larguraButton) // 2
        start_y = (tamanho[1] // 2) 
        quit_y = start_y + 70

        startButton = pygame.draw.rect(tela, branco, (centro_x, start_y, larguraButton, alturaButton), border_radius=15)
        startTexto = fonteMenu.render("Jogar Novamente", True, preto)
        tela.blit(startTexto, startTexto.get_rect(center=startButton.center))

        quitButton = pygame.draw.rect(tela, branco, (centro_x, quit_y, larguraButton, alturaButton), border_radius=15)
        quitTexto = fonteMenu.render("Sair do Game", True, preto)
        tela.blit(quitTexto, quitTexto.get_rect(center=quitButton.center))

        pygame.display.update()
        relogio.tick(60)

def tela_boas_vindas(nome_jogador):
    larguraButtonStart = 200
    alturaButtonStart = 50
    fundoWelcome = pygame.image.load("assets/fundoJogo.png")

    while True:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                quit()
            elif evento.type == pygame.MOUSEBUTTONUP:
                mouse_pos = pygame.mouse.get_pos()
                if startButton.collidepoint(mouse_pos):
                    return 

        tela.fill(branco)
        tela.blit(fundoWelcome, (0, 0))

        texto_bem_vindo = fonteMenu.render(f"Olá, {nome_jogador}!", True, branco)
        texto_instrucoes1 = fonteMenu.render("Use as SETAS para se mover.", True, branco)
        texto_instrucoes2 = fonteMenu.render("Desvie dos chopps envenenados do Evil Marcão.", True, branco)
        texto_instrucoes3 = fonteMenu.render("Pressione ESPAÇO para pausar o jogo.", True, branco)

        centro_tela_x = tamanho[0] / 2
        tela.blit(texto_bem_vindo, texto_bem_vindo.get_rect(center=(centro_tela_x, 250)))
        tela.blit(texto_instrucoes1, texto_instrucoes1.get_rect(center=(centro_tela_x, 300)))
        tela.blit(texto_instrucoes2, texto_instrucoes2.get_rect(center=(centro_tela_x, 330)))
        tela.blit(texto_instrucoes3, texto_instrucoes3.get_rect(center=(centro_tela_x, 360)))

        start_x = centro_tela_x - (larguraButtonStart / 2)
        startButton = pygame.draw.rect(tela, branco, (start_x, 450, larguraButtonStart, alturaButtonStart), border_radius=15)
        startTexto = fonteMenu.render("Iniciar Partida", True, preto)
        tela.blit(startTexto, startTexto.get_rect(center=startButton.center))

        pygame.display.update()
        relogio.tick(60)

start()