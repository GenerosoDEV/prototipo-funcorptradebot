import asyncio, json, time
from aiotfm.client import Client, Inventory
from aiotfm import enums

QUEIJO_ID = 0 # Preciso pegar o ID do consumível do queijo
sacadores_autorizados = []

client = Client()

boot_time = client.loop.time()


@client.event
async def on_login_ready(*a):
	await client.login(username="", password="", room="*funcorp br donate") # Loga no usuário da funcorp


@client.event
async def on_ready():
	print(f'Conectado ao Transformice [{client.loop.time() - boot_time:.2f}s]') # Avisa nas logs que está conectado
	

@client.event
async def on_room_message(message):
    if message.content == 'queijo': # Se o usuário quiser doar queijo
        await client.whisper(username=message.author.username, message="Em alguns segundos enviarei uma solicitação de troca. Você terá 1 minuto para colocar 200 queijos, ou a troca será cancelada! Após colocar os 200 queijos, confirme a troca!", overflow=True) # Avisa como funciona a doação
        await asyncio.sleep(3) # Espera 3 segundos para começar a troca
        trade = await client.startTrade(message.author) # Envia a troca
        sended = time.time() # Anota a hora que enviou a troca
        while True: # Inicia um loop de verificação
            if trade.closed():
                await client.whisper(username=message.author.username, message="Que pena que você desistiu de fazer a doação... :/", overflow=True) # Avisa do cancelamento da troca
                break
            elif trade.state == enums.TradeState.ON_INVITE: # Se ainda estiver pendente o convite
                if time.time() - sended > 15: # Verifica se o convite foi enviado há mais de 15 segundos
                    await client.whisper(username=message.author.username, message="Já se passaram 15 segundos do envio da oferta de troca, você desistiu? :/", overflow=True) # Avisa do cancelamento da troca
                    await client.whisper(username=message.author.username, message='Caso você ainda deseja fazer uma doação, envie "queijo" novamente.', overflow=True) # Avisa do cancelamento da troca
                    break # Para de verificar, se foi enviado há mais de 15 segundos
            elif trade.state == enums.TradeState.TRADING: # Verifica se já está sendo trocado
                    started_trade = time.time() #  Anota a hora que começou a troca
                    while True: # Inicia um 2º loop de verificação
                        if trade.locked[0] is True: # Verifica se o jogador já travou a troca
                            # Puxa o que o jogador está ofertando, se for 200 queijos, aceita e dá os direitos de doador, se não, cancela a troca e avisa no privado
                            itens_para_receber = trade.imports
                            if itens_para_receber.get(QUEIJO_ID) == 200:
                                await trade.lock()
                                await client.whisper(username=message.author.username, message="A equipe Funcorp BR agradece pela sua doação! Caso você ainda não tenha seu discord vinculado, entre em contato com um membro da equipe. Caso contrário, você já recebeu seus direitos de doador!", overflow=True)
                                # ENVIA NUM WEBHOOK QUE ESSA PESSOA VIROU DOADORA 
                                # ENVIA NUM OUTRO WEBHOOK O SALDO ATUAL DE QUEIJOS (FICAR ATENTO PARA NAO ATINGIR 1500)
                                break
                            else:
                                await trade.cancel() # Cancela a troca
                                await client.whisper(username=message.author.username, message="Sua troca foi cancelada pois você não colocou os 200 queijos!", overflow=True) # Avisa do cancelamento da troca
                                break
                        elif time.time() - started_trade > 60: # Verifica se já se passaram 60 segundos do início da troca
                            await trade.cancel() # Cancela a troca
                            await client.whisper(username=message.author.username, message="Sua troca foi cancelada pois está sendo operada há mais de 60 segundos!", overflow=True) # Avisa do cancelamento da troca
                            break
                    break
    elif message.content == "sacarqueijos":
        if message.author.username in sacadores_autorizados:
            quantidade_de_queijos = Inventory.items[QUEIJO_ID].quantity # Salva a quantidade de queijos
            trade = await client.startTrade(message.author) # Envia a troca
            sended = time.time() # Anota a hora que enviou a troca
            while True: # Inicia um loop de verificação
                if trade.closed(): # Se fechou a troca
                    break # Para o loop
                elif trade.state == enums.TradeState.ON_INVITE: # Se ainda estiver pendente o convite
                    if time.time() - sended > 15: # Verifica se o convite foi enviado há mais de 15 segundos
                        break # Para de verificar, se foi enviado há mais de 15 segundos
                elif trade.state == enums.TradeState.TRADING: # Verifica se já está sendo trocado
                        started_trade = time.time() #  Anota a hora que começou a troca
                        await trade.addItem(QUEIJO_ID, quantidade_de_queijos) # Adiciona os queijos
                        await trade.lock() # Aceita a troca
                        while True:
                            if trade.state != enums.TradeState.SUCCESS:
                                # ENVIA NUM WEBHOOK QUE ESSA SACADOR AUTORIZADO SACOU X QUANTIDADE DE QUEIJOS
                                # ENVIA NUM OUTRO WEBHOOK O SALDO ATUAL DE QUEIJOS (FICAR ATENTO PARA NAO ATINGIR 1500)
                                break # Quando a troca for confirmada
                            elif time.time() - started_trade > 60: # Verifica se já se passaram 60 segundos do início da troca
                                await trade.cancel() # Cancela a troca
                                break
                        break

            

loop = asyncio.get_event_loop()
loop.create_task(client.start())

loop.run_forever()
