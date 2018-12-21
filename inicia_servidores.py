# -*- coding: utf-8 -*-
import argparse
import os
import yaml
import subprocess
import time

CONFIGS = yaml.load(open('configs.yml', 'r'))
process = []

def salva_servidores(servers):
    caminho = CONFIGS['SERVIDORES']
    with open(caminho, "w") as file:
        s = ['{}'.format(s) for s in servers]
        file.write("\n".join(s))

def salva_parametros(params):
    caminho = CONFIGS['DB_PARAMS']
    yaml.dump(params, open(caminho, "w"), default_flow_style=False)

def tem_resto(a, b):
    return True if a % b > 0 else False

def calcula_faixas(m, n):
    dois_a_m = 2 ** m
    divisor  = dois_a_m // n
    primeiro = divisor if tem_resto(dois_a_m, n) else divisor - 1

    faixas = list(range(primeiro, dois_a_m, divisor))
    limite = dois_a_m - 1
    ultimo = faixas[n - 1]

    if ultimo < limite:
        faixas[n - 1] = limite

    return faixas

def inicia_servidor(atual, ant, post, bash=None, bash_params=None):
    if bash == None:
        bash = CONFIGS['BASH']

    if bash_params == None:
        bash_params = CONFIGS['BASH_PARAMS']

    bash_params = bash_params.format(atual)

    comando_python = '{} servidor.py {} {} {}'.format(CONFIGS['PYTHON'], atual, 
        ant, post)

    print 'Código do servidor: {}'.format(atual)

    comando = "{} {} -e '{}'  &".format(bash,  bash_params,comando_python) # DETACHED

    if bash.startswith('gnome'):
        comando = "{} {} -- bash -c '{}'  &".format(bash,  bash_params,comando_python) # DETACHED

    my_env = os.environ.copy()
    
    #inicializa bootstrap
    p = subprocess.Popen(['concoord', 'replica','-o', 'banco_de_dados.BancoDeDados','-a', '127.0.0.1', '-p', CONFIGS['PREFIXO_PORTA']+ str(atual) + str(0)],env=dict(os.environ, PYTHONPATH=":/"))

    time.sleep(3)
    process.append(p)

    #inicializa as replicas
    for i in range(1,3):
        my_env = os.environ.copy()  
        my_env["PYTHONPATH"] = "/:" + my_env["PATH"] 
        p = subprocess.Popen(['concoord', 'replica','-o', 'banco_de_dados.BancoDeDados','-b', '127.0.0.1:'+CONFIGS['PREFIXO_PORTA'] + str(atual) + str(i),'-a', '127.0.0.1', '-p', CONFIGS['PREFIXO_PORTA']+ str(atual) + str(i)],env=dict(os.environ, PYTHONPATH=":/"))

    process.append(p)
    os.system('export PYTHONPATH=$PYTHONPATH')
    print 'Código do servidor: Inicia servidor {}'.format(atual)

    os.system(comando)
    time.sleep(5)

    

def inicia_servidores(m, n, bash=None, bash_params=None):
    servers = calcula_faixas(m, n)
    salva_servidores(servers)

    for srv in range(n):
        atual = servers[srv]
        ant   = servers[srv - 1]

        try:
            post = servers[srv + 1]
        except IndexError:
            post = servers[0]

        inicia_servidor(atual, ant, post, bash, bash_params)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("bits", 
        help="m-bits para chave (M)", 
        type=int)
    parser.add_argument("servers", 
        help="quantidade de servers (N)", 
        type=int)
    parser.add_argument("--bash", "-bsh",
        help="Bash/Terminal LINUX a ser usado", 
        type=str)
    parser.add_argument("--bash-params", "-bsh-params",
        help="Parâmetros bash", 
        type=str)

    args = parser.parse_args()

    salva_parametros(vars(args))
    inicia_servidores(m=args.bits, n=args.servers, 
                      bash=args.bash, bash_params=args.bash_params)
    x = raw_input()

if __name__ == '__main__':
    try:
        main()
    except:
        for p in process:
            p.kill()
    