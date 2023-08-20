using Microsoft.AspNetCore.Authentication.Cookies;
using Microsoft.AspNetCore.DataProtection;
using Microsoft.AspNetCore.Server.Kestrel.Core;

using spaces;

var builder = WebApplication
    .CreateBuilder(args);

builder.WebHost
    .UseKestrel(options =>
    {
        options.ListenAnyIP(5000);
        options.Limits.MaxRequestBodySize = 0L;
        options.Limits.MaxRequestHeadersTotalSize = 8192;
        options.Limits.MinRequestBodyDataRate = new MinDataRate(1024.0, TimeSpan.FromSeconds(3));
    })
    .UseShutdownTimeout(TimeSpan.FromSeconds(5));

builder.Services
    .AddDataProtection()
    .PersistKeysToFileSystem(new DirectoryInfo("settings"))
    .SetApplicationName(nameof(spaces));

builder.Services
    .AddAuthentication(CookieAuthenticationDefaults.AuthenticationScheme)
    .AddCookie(CookieAuthenticationDefaults.AuthenticationScheme, options =>
    {
        options.Cookie.SameSite = SameSiteMode.Strict;
        options.Cookie.Name = "usr";
    });

var app = builder.Build();

app.Lifetime.ApplicationStopping.Register(WsHandler.CloseConnections);

app
    .UseDefaultFiles()
    .UseStaticFiles()
    .UseAuthentication()
    .UseUserId()
    .UseWebSockets(new WebSocketOptions { KeepAliveInterval = TimeSpan.FromSeconds(30) });

app.Map("/ws", async ctx =>
{
    if(!ctx.WebSockets.IsWebSocketRequest)
    {
        ctx.Response.StatusCode = StatusCodes.Status400BadRequest;
        return;
    }

    using var webSocket = await ctx.WebSockets.AcceptWebSocketAsync();
    await WsHandler.MessageLoopAsync(webSocket, ctx.User.FindUserId(), ctx.RequestAborted);
});

app.Run();
