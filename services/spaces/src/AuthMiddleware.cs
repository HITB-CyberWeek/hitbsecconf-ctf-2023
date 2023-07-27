using System.Security.Claims;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Authentication.Cookies;

namespace spaces;

internal class AuthMiddleware
{
    public AuthMiddleware(RequestDelegate next) => this.next = next;

    public async Task Invoke(HttpContext context)
    {
        await SignInAsync(context);
        await next.Invoke(context);
    }

    private static async Task SignInAsync(HttpContext context)
    {
        if(context.User.FindUserId() != default)
            return;

        var id = Guid.NewGuid().ToString("N");
        var principal = new ClaimsPrincipal(new ClaimsIdentity(EnumerableHelper.Yield<Claim>(new(ClaimTypes.Name, id)), CookieAuthenticationDefaults.AuthenticationScheme));
        context.User = principal;

        await context.SignInAsync(CookieAuthenticationDefaults.AuthenticationScheme, principal);
    }

    private readonly RequestDelegate next;
}

public static class AuthMiddlewareExtensions
{
    public static IApplicationBuilder UseUserId(this IApplicationBuilder builder)
        => builder.UseMiddleware<AuthMiddleware>();
}

public static class AuthController
{
    public static Guid FindUserId(this ClaimsPrincipal? principal)
        => Guid.TryParseExact(principal?.Identity?.Name, "N", out var id) ? id : default;
}
