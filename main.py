import os
import logging
import nest_asyncio
from autogen_agentchat.agents import AssistantAgent, CodeExecutorAgent
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class HealthcareAgent:
    def __init__(self):
        """Inicializa os agentes e configura o ambiente."""
        logging.info("Inicializando os agentes de IA...")

        # Carrega as variáveis de ambiente
        endpoint = os.getenv("ENDPOINT_URL")
        deployment = os.getenv("DEPLOYMENT_NAME")
        subscription_key = os.getenv("AZURE_OPENAI_API_KEY")
        api_version = os.getenv("API_VERSION")

        # Inicializa o cliente Azure OpenAI
        self.client = AzureOpenAIChatCompletionClient(
            azure_endpoint=endpoint,
            model=deployment,
            api_key=subscription_key,
            api_version=api_version,
        )
        logging.info(f"Cliente Azure OpenAI configurado com endpoint: {endpoint} e deployment: {deployment}")

        # Inicializa os agentes com o cliente configurado
        self.assistant_agent = AssistantAgent("MedicalAssistant", self.client)
        self.code_executor_agent = CodeExecutorAgent("ContextIdentifier", self.client)

        # Caminhos para os arquivos de dados
        self.files = {
            "medical_record": "./data/medical_record.txt",
            "image_record": "./data/image_record.txt",
            "lab_record": "./data/lab_record.txt",
        }

    async def identify_context(self, question: str):
        """Usa CodeExecutorAgent para identificar o contexto correto."""
        logging.info(f"Usando CodeExecutorAgent para identificar contexto da pergunta: '{question}'")

        context_prompt = f"""
        Você é um assistente especializado em identificar o contexto correto de uma pergunta médica. 
        Considere os seguintes contextos disponíveis:
        - 'medical_record': informações gerais sobre o histórico médico do paciente.
        - 'image_record': registros relacionados a imagens médicas (como ressonâncias ou radiografias).
        - 'lab_record': resultados de exames laboratoriais (como exames de sangue ou urina).

        Abaixo está a pergunta do usuário:
        "{question}"

        Retorne uma lista dos contextos relevantes (por exemplo: ['medical_record'], ['image_record', 'lab_record']) 
        com base na pergunta.
        """
        logging.info("Enviando tarefa para o agente 'ContextIdentifier'...")
        response = await self.code_executor_agent.run(task=context_prompt)
        logging.info(f"Contextos identificados: {response}")
        return response

    async def handle_contexts(self, contexts, question):
        """Lida com múltiplos contextos e combina resultados."""
        combined_records = []
        
        for context in contexts:
            file_path = self.files.get(context.strip())
            if not file_path or not os.path.exists(file_path):
                logging.error(f"Arquivo não encontrado: {file_path}")
                continue

            logging.info(f"Lendo o arquivo: {file_path}")
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    record = file.read()
                    combined_records.append((context, record))
            except FileNotFoundError:
                logging.error(f"Arquivo não encontrado: {file_path}")

        if not combined_records:
            logging.warning("Nenhuma informação relevante foi encontrada nos registros.")
            return "Nenhuma informação relevante foi encontrada nos registros."

        logging.info("Criando o prompt para o agente 'MedicalAssistant'...")
        combined_text = "\n\n".join([f"Contexto: {context}\n{record}" for context, record in combined_records])
        task_prompt = f"""
        Você é um assistente virtual especializado em fornecer informações detalhadas com base em diferentes fontes de dados. 
        Abaixo estão os registros relevantes do paciente:

        {combined_text}

        Responda à pergunta do usuário com base nos registros combinados:
        Pergunta do usuário: "{question}"
        """
        logging.info("Enviando tarefa para o agente 'MedicalAssistant'...")
        response = await self.assistant_agent.run(task=task_prompt)
        return response

    async def run(self, question):
        """Gerencia o fluxo principal com base na pergunta do usuário."""
        logging.info("Processando a pergunta do usuário...")
        contexts = await self.identify_context(question)

        # Transforma o resultado do agente em uma lista utilizável
        try:
            contexts = eval(contexts) if isinstance(contexts, str) else contexts
        except Exception as e:
            logging.error(f"Erro ao processar os contextos identificados: {e}")
            return "Ocorreu um erro ao identificar os contextos relevantes."

        return await self.handle_contexts(contexts, question)


# Função principal
async def main():
    # Corrige o ambiente de loop para evitar erros
    nest_asyncio.apply()

    # Inicializa o agente de saúde
    healthcare_agent = HealthcareAgent()

    while True:
        user_question = input("Digite sua pergunta (ou 'exit' para sair): ")
        if user_question.lower() == "exit":
            logging.info("Encerrando o programa...")
            break

        logging.info("Processando a pergunta do usuário...")
        response = await healthcare_agent.run(user_question)
        logging.info("Resposta processada com sucesso.")
        print("\n[INFO] Resposta do assistente:")
        print(response)


# Executa a função principal
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
