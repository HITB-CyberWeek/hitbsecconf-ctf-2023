<html>
	<head>
		<title>CTF Password Manager Service</title>
		<style>
		h1 {
			text-align: center;
		}
		div {
			margin-bottom: 10px;
		}
		.buttons {
			margin: 20px 0 0 155px;
		}
		.buttons input {
			padding: 10px 15px;
		}
		.error {
			border: 1px solid darkred;
			background: salmon;
		}
		.info {
			border: 1px solid darkgreen;
			background: #73ECFA;
		}
		label {
 			display: inline-block;
 			width: 150px;
 			text-align: right;
 		}
		input[name="login"] {
			border-radius: 2px;
			background-color: #88B04B;
		}
		input[name="register"] {
			border-radius: 2px;
			background-color: #92A8D1;
		}
		input[name="logout"] {
			border-radius: 2px;
			background-color: #92A8D1;
		}
		</style>
	</head>

	<body>
		<h1>CTF Password Manager Service</h1>

		<form action="/" method="POST">
			<div>
				<label>Username:</label>
				<input type="text" name="user" maxlength="20" placeholder="required" autofocus/>
			</div>

			<div>
				<label>Password:</label>
				<input type="password" name="password" maxlength="20" placeholder="required"/>
			</div>

			<div class="buttons">
				<input type="submit" name="login"    value="Login" />
				<input type="submit" name="register" value="Register" />
			</div>
		</form>

		{{ if .Error }}

		<div class="error"> <i>&#9888;</i> {{ .Error }} </div>

		{{ end }}

		{{ if .Info }}

		<div class="info"> &#9432; {{ .Info }} </div>

		{{ end }}
	</body>
</html>
