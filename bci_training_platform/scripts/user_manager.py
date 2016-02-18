#!/usr/bin/env python
from threading import Thread
from scipy import signal as sig
import sys, os, rospy, rospkg
import numpy as np
from std_msgs.msg import Float64MultiArray, Float64, MultiArrayDimension, String
from itertools import combinations

#funcao que calcula a covariancia normalizada da matriz de sinais X
def cov_(X):
	cov = X*X.T
	return cov/cov.trace()


#define a classe manager
class manager:
	def __init__(self):
		#cria o node do ros
		rospy.init_node('manager', anonymous=True)
		#cria o subscriber do node para o canal com a interfce grafica
		rospy.Subscriber('manager_gui', String, self.callback_manager_gui, queue_size=10)
		#cria o publisher do node
		self.pub=rospy.Publisher('manager_gui', String, queue_size=100)
		#cria o subscriber do node para o canal com as amostras
		rospy.Subscriber('manager_smp', Float64MultiArray, self.callback_manager_smp, queue_size=30)
		#caminho global para este arquivo
		self.globalpath=os.path.abspath(os.path.dirname(__file__))
		
		#define variaveis e parametros
		self.loop=1
		self.user=""
		self.task=0
		self.parameters_1()
		self.parameters_2()
		self.parameters_4()
		
		#define o filtro FIR a ser utilizado
		self.fir=np.matrix(sig.firwin(21,[8,30],pass_zero=False,nyq=125.0))
		
		#cria o loop do node
		while self.loop==1:
			pass
			
	#parametros para a etapa de calibraçao		
	def parameters_1(self):
		self.alert_time = 0
		self.cue_time = 0
		self.task_time = 0
		self.pause_time = 0
		self.classes=[]
		self.number_trials=0
		self.feature_window_0=0
		self.feature_window_1=0
		self.number_samples=0
		self.status=0
		self.count=0
		
	#parametros para a etapa de teste de classificaçao	
	def parameters_2(self):
		self.alert_time2 = 0
		self.cue_time2 = 0
		self.task_time2 = 0
		self.pause_time2 = 0
		self.classes2=[]
		self.number_trials2=0
		self.feature_window_02=0
		self.feature_window_12=0
		self.number_samples2=0

	#parametros para a etapa de treinamento do usuario
	def parameters_4(self):
		self.win_size = 0
		self.win_displacement = 0
		
	#callback para o subscriber do canal entre a interface gráfica
	#a interface gráfica envia comandos para esse node através de mensagens do tipo string pelo canal
	def callback_manager_gui(self,msg):
		#recebe o usuario por mensagem "USnome_do_usuario"
		if msg.data[0:2]=="US":
			self.user=msg.data[2:]
			print(self.user)

		#define tarefa de calibração a ser executada
		elif msg.data[0:2]=="NC":
			#seleciona primeira tarefa
			self.task=1
			#abre o arquivo para salvar as amostras
			self.file0=open(self.globalpath + "/users/%s/samples.txt" %self.user,'a')
			#carrega os parametros definidos na interface gráfica para a calibração
			self.load_parameters_1()
			#usa os parametros e calcula o número total de amostras a serem recebidas
			self.number_samples=((int(self.alert_time)+int(self.cue_time)+int(self.task_time)+int(self.pause_time))*int(self.number_trials)*len(self.classes)*250)/1000

		#define tarefa de teste de classificaçao a ser executada
		elif msg.data[0:2]=="T1":
			#seleciona segunda tarefa
			self.task=2
			#cria arquivo para salvar as amostras
			self.file1=open(self.globalpath + "/users/%s/test1.txt" %self.user,'w')
			#carrega parametros definidos na interface gráfica para o teste
			self.load_parameters_2()
			#carrega os valores CSP e LDA obtidos pela calibraçao
			self.loadparams()
			#usa os parametros e calcula o número de amoastras por ensaio a serem recebidas
			self.number_samples=((int(self.alert_time2)+int(self.cue_time2)+int(self.task_time2)+int(self.pause_time2))*250)/1000
			#cria um buffer para as amostras
			self.buffer=np.matrix([[0]*8]*self.number_samples).T

		#define tarefa de treinamento do usuario a ser executada
		elif msg.data[0:2]=="GA":
			#seleciona quarta tarefa(nao ter terceira tarefa)
			self.task=4
			#carrega os parametros definidos na interface gráfica para o treinamento
			self.load_parameters_4()
			#carrega os calores CSP e LDA obtidos pela calibraçao
			self.loadparams()
			#cria o buffer para a janela de amostras
			self.number_samples = int(self.win_size)*250//1000
			self.buffer=np.matrix([[0]*8]*self.number_samples).T
			
		#comando enviado pela interface gráfica que inicia uma das tres tarefas (1 2 ou 4)	
		elif msg.data[0:2]=="XX" and self.user!="":
			self.status=1
			
		#comando enviado pela interface gráfica que finaliza uma tarefa	
		elif msg.data[0:2]=="XY" and self.user!="":
			self.status=0
			self.task=0
			
		#comando que finaliza esse node(sai do loop)	
		elif msg.data[0:2]=="DY":
			self.loop=0
	
	#callback para lidar com as amostras, também define as 3 tarefas
	def callback_manager_smp(self,msg):
	
		#primera tarefa
		if self.task==1 and self.status==1:
			self.count+=1
			#append um vetor de amostras no arquivo
			self.file0.write("".join([str(y)+'\t' for y in np.matrix(msg.data).T.A1])[0:-1]+'\n')		
			#ao atingir o número totas entra aqui
			if self.count == self.number_samples:
				self.status=0
				self.count=0
				self.file0.close()
				#chama a função que calcula o CSP e LDA
				self.calcparams()
				print("ok")
				
		#segunda tarefa		
		elif self.task==2 and self.status==1:
			self.count+=1
			#append um vetor de amostras no arquivo
			self.file1.write("".join([str(y)+'\t' for y in np.matrix(msg.data).T.A1])[0:-1]+'\n')	
			#self.buffer=np.hstack((self.buffer,np.matrix(msg.data).T))
			#self.buffer=np.delete(self.buffer,0,1)
			
			#entra aqui ao final de cada ensaio
			if self.count == self.number_samples:
				self.file1.close()
				self.status=0
				self.count=0
				#print("done")
				#print("self.number_samples")
				X=self.importa(self.globalpath+'/users/%s/test1.txt' %self.user)
				#print(X.T[0])
				#print(X.T[2249])
				
				#classifica o ensaio
				self.temp=np.matrix(sig.convolve(X,self.fir))
				self.temp=self.temp.T[250*int(self.feature_window_02)//1000:250*int(self.feature_window_12)//1000].T
				self.temp=cov_(self.temp)
				self.temp=self.W_csp*self.temp*self.W_csp.T
				self.temp=np.matrix((np.log10(np.diag(self.temp))).T)
				self.temp=self.temp*self.W_lda
				
				#envia a classificação para a interface gráfica
				if self.temp>self.L:
					self.pub.publish('RT0')
				elif self.temp<self.L:
					self.pub.publish('RT1')
				
				#limpa o arquivo das amostras
				self.file1=open(self.globalpath + "/users/%s/test1.txt" %self.user,'w')
				
				#envia mensagem para a interface gráfica sinalizando que pode começar outro ensaio
				self.pub.publish('TT')
				#print(self.temp)
				
				
				
		#quarta tarefa		
		elif self.task==4 and self.status==1:
			self.count+=1
			#armazena o vetor de amostras no buffer
			self.buffer=np.hstack((self.buffer,np.matrix(msg.data).T))
			self.buffer=np.delete(self.buffer,0,1)
			
			#entra aqui quando o vetor estiver cheio
			if self.count == self.number_samples + int(self.win_displacement)*250//1000:
				self.status=0
				self.temp=self.buffer
				self.count=self.number_samples
				self.status=1		
				#classifica o buffer
				self.temp=np.matrix(sig.convolve(self.temp,self.fir))
				self.temp=self.temp.T[250*3:250*6].T
				self.temp=cov_(self.temp)
				self.temp=self.W_csp*self.temp*self.W_csp.T
				self.temp=np.matrix((np.log10(np.diag(self.temp))).T)
				self.temp=self.temp*self.W_lda			
				#envia a classificaçao para a interface gráfica
				if self.temp>self.L:
					self.pub.publish('TX+1')
				elif self.temp<self.L:
					self.pub.publish('TX-1')
				#print(self.temp)

			
	#funcao que carrega o arquivo de parametros 1		
	def load_parameters_1(self):
		try:
			file=open(self.globalpath + "/users/" + self.user + "/" + "parameters_1.txt",'r')
		except:
			file=open(self.globalpath + "/users/" + self.user + "/" + "parameters_1.txt",'w')
		file=open(self.globalpath + "/users/" + self.user + "/" + "parameters_1.txt",'r')	
		self.alert_time = file.readline()[0:-1]
		self.cue_time = file.readline()[0:-1]
		self.task_time = file.readline()[0:-1]
		self.pause_time = file.readline()[0:-1]
		self.classes=[int(x) for x in file.readline()[0:-1].split(" ")]
		self.number_trials=file.readline()[0:-1]
		self.feature_window_0=file.readline()[0:-1]
		self.feature_window_1=file.readline()[0:-1]
		file.close()

	#funcao que carrega o arquivo de parametros 2	
	def load_parameters_2(self):
		try:
			file=open(self.globalpath + "/users/" + self.user + "/" + "parameters_2.txt",'r')
		except:
			file=open(self.globalpath + "/users/" + self.user + "/" + "parameters_2.txt",'w')
		file=open(self.globalpath + "/users/" + self.user + "/" + "parameters_2.txt",'r')	
		self.alert_time2 = file.readline()[0:-1]
		self.cue_time2 = file.readline()[0:-1]
		self.task_time2 = file.readline()[0:-1]
		self.pause_time2 = file.readline()[0:-1]
		self.classes2=[int(x) for x in file.readline()[0:-1].split(" ")]
		self.number_trials2=file.readline()[0:-1]
		self.feature_window_02=file.readline()[0:-1]
		self.feature_window_12=file.readline()[0:-1]
		file.close()
		
	#funcao que carrega o arquivo de parametros 4
	def load_parameters_4(self):
		try:
			file=open(self.globalpath + "/users/" + self.user + "/" + "parameters_4.txt",'r')
		except:
			file=open(self.globalpath + "/users/" + self.user + "/" + "parameters_4.txt",'w')
			self.save_parameters_4()
		file=open(self.globalpath + "/users/" + self.user + "/" + "parameters_4.txt",'r')	
		self.win_size = file.readline()[0:-1]
		self.win_displacement = file.readline()[0:-1]
		file.close()

	#funcao que calcula o CSP e LDA
	def calcparams(self):
		print('calc params')
		#importa o arquivo de amostras
		X=self.importa(self.globalpath+'/users/%s/samples.txt' %self.user)
		#X=X[0:8] (seleciona 8 canais)
		
		#importa as marcações
		Y=self.importa(self.globalpath+'/users/%s/marcas.txt' %self.user)
		ind_T = np.argsort(Y[1].A1)
		Y[1] = Y[1].A1[ind_T]
		Y[0] = Y[0].A1[ind_T]
		X_bp=np.matrix(sig.convolve(X,self.fir))
		X_T=[X_bp.T[y+250*int(self.feature_window_0)/1000:y+250*int(self.feature_window_1)/1000].T for y in Y.tolist()[0]]
		Xa = X_T[0:int(self.number_trials)]          #array de matrizes de sinais da classe a
		Xb = X_T[int(self.number_trials):int(self.number_trials*2)]          #array de matrizes se sinais da classe b
		Ca_ = [cov_(X) for X in Xa]                  #array de matrizes de covariancia da classe a
		Cb_ = [cov_(X) for X in Xb]
		Ca = sum(Ca_)/len(Ca_)
		Cb = sum(Cb_)/len(Cb_)
		C = Ca + Cb
		U,V = np.linalg.eigh(C)
		V = V[:,np.argsort(U)]
		U = np.matrix(np.diag(U[np.argsort(U)]))
		Q = np.sqrt(U.I)*V.T	
		U2,V2 = np.linalg.eigh(Q*Ca*Q.T)
		V2 = V2[:,np.argsort(U2)]
		W = V2.T*Q
		W_n = 3
		W_ = W[np.arange(W_n).tolist() + \
			sorted((-1-np.arange(W_n)).tolist())]    #separa os 3 primeiros e os tres ultimos filtros espaciais
		self.W_csp=W_
		Za = np.matrix((np.log10([np.diag(x) for x in [W_*X*W_.T for X in Ca_]])).T)
		Zb = np.matrix((np.log10([np.diag(x) for x in [W_*X*W_.T for X in Cb_]])).T)
		Ma, Mb = (sum(Za.T).T/len(Za.T)), (sum(Zb.T).T/len(Zb.T))
		Sa, Sb = (Za*Za.T - Ma*Ma.T), (Zb*Zb.T - Mb*Mb.T)
		W2 = (Sa + Sb).I * (Ma - Mb)
		self.W_lda=W2
		L = W2.T * (Ma + Mb) * 0.5
		self.L=L
		print(L)
		#cria arquivo para os parametros
		self.file3=open(self.globalpath + "/users/%s/calibration.txt" % self.user,'w')
		print(W_)
		print(W2)
		
		#salva os parametros
		for element in W_:
			self.file3.write("".join([str(y)+'\t' for y in element.A1])[0:-1]+'\n')
		for element2 in W2:
			self.file3.write("".join([str(y)+'\t' for y in element2.A1]))
		self.file3.write("%s\t%s\n" %(L.A1[0],L.A1[0]))
		self.file3.close()
		print('did')

		
	#funcao que carrega os parametros CSP e LDA
	def loadparams(self):
		W_csp = (self.importa(self.globalpath + "/users/%s/calibration.txt" % self.user)).T
		W_lda = (W_csp[-1]).T[0:6]
		L=(W_csp[-1]).T[-1]
		W_csp = W_csp[0:-1]
		self.W_csp=W_csp
		self.W_lda=W_lda
		self.L=L
		
	#funcao geral que importa arquivos de amostras e marcaçoes na forma de matriz
	def importa(self,nome_do_arquivo):
		return np.matrix([[float(x) for x in y] for y in [y.split('\t') \
			for y in open(nome_do_arquivo,'r').read().split('\n')[0:-1]]]).T


		
		
a=manager()

