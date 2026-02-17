# ---------- Build stage ----------
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src

# Copy csproj
COPY ./src/CalculatorApi.csproj ./
RUN dotnet restore CalculatorApi.csproj

# Copy the rest of the source
COPY ./src/ ./

# Publish
RUN dotnet publish -c Release -o /publish

# ---------- Runtime stage ----------
FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS final
WORKDIR /app

COPY --from=build /publish .

EXPOSE 80
ENV ASPNETCORE_URLS=http://+:80

ENTRYPOINT ["dotnet", "CalculatorApi.dll"]