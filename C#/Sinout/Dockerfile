# Usa a imagem oficial do SDK do .NET 8.0 para compilar o projeto
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src

# Copia o arquivo de projeto e restaura as dependências
# Ajuste "Sinout.csproj" se o nome do seu arquivo for diferente
COPY ["Sinout.csproj", "./"]
RUN dotnet restore "Sinout.csproj"

# Copia todo o resto do código fonte
COPY . .

# Compila e publica a versão final (Release) na pasta /app/publish
RUN dotnet publish "Sinout.csproj" -c Release -o /app/publish

# ETAPA 2: Runtime (Execução)
# Usa apenas a imagem leve de runtime (sem o SDK pesado)
FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS final
WORKDIR /app

# Expõe a porta 80 (padrão do container)
EXPOSE 80

# Copia os arquivos compilados da etapa anterior
COPY --from=build /app/publish .

# Define o comando que inicia a API
ENTRYPOINT ["dotnet", "Sinout.dll"]