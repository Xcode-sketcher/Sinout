# Usa a imagem oficial do .NET 10.0
FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src

# Copia o arquivo de projeto e restaura as dependências
COPY ["Sinout.csproj", "./"]
RUN dotnet restore "Sinout.csproj"

# Copia todo o resto do código fonte
COPY . .

# Compila e publica a versão final na pasta /app/publish
RUN dotnet publish "Sinout.csproj" -c Release -o /app/publish


# Usa apenas a imagem de runtime
FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS final
WORKDIR /app

# Expõe a porta 80 (padrão do container)
EXPOSE 80

# Copia os arquivos compilados da etapa anterior
COPY --from=build /app/publish .

# Define o comando que inicia a API
ENTRYPOINT ["dotnet", "Sinout.dll"]