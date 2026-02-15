# ---------- Build stage ----------
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src

# Copy csproj and restore
COPY ../src/ControllerApi.csproj .
RUN dotnet restore ControllerApi.csproj

# Copy the rest of the source code
COPY ../src .

# Publish
RUN dotnet publish -c Release -o /publish

# ---------- Runtime stage ----------
FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS final
WORKDIR /app

# Copy published output
COPY --from=build /publish .

EXPOSE 80
ENV ASPNETCORE_URLS=http://+:80

ENTRYPOINT ["dotnet", "ControllerApi.dll"]