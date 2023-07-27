using Microsoft.AspNetCore.Authentication.Cookies;
using Microsoft.AspNetCore.DataProtection;
using spaces;

var builder = WebApplication
    .CreateBuilder(args);

builder.WebHost
    .UseKestrel(options => { options.ListenLocalhost(5000); })
    .UseShutdownTimeout(TimeSpan.FromSeconds(3));

builder.Services
    .AddDataProtection()
    .PersistKeysToFileSystem(new DirectoryInfo("settings")).SetApplicationName(nameof(spaces));

builder.Services
    .AddAuthentication(CookieAuthenticationDefaults.AuthenticationScheme)
    .AddCookie(CookieAuthenticationDefaults.AuthenticationScheme, options =>
    {
        options.Cookie.SameSite = SameSiteMode.Strict;
        options.Cookie.Name = "usr";
    });

var app = builder.Build();

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
    await WebSocketHandler.MessageLoopAsync(webSocket, ctx.User.FindUserId(), ctx.RequestAborted);
});

app.Run();
