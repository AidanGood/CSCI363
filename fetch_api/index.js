function getNewDog() {
	var url = "https://dog.ceo/api/breed/borzoi/images/random"

	console.log("making fetch to", url)
	
	fetch(url)
		.then(resp=>{return resp.json()})
		.then(json=>{
			console.log(json)

			document.getElementById("dogImage").src = json.message
		})

}

function getCatFact() {
    var url = "https://cat-fact.herokuapp.com/facts/random"

    console.log("making fetch to", url)

    fetch(url)
        .then(resp=>{return resp.json()})
        .then(json=>{
            console.log(json)

            document.getElementById("catFact").innerHTML = json.text
    })

}


function getPoem() {
    var url = "https://poetrydb.org/random"

    console.log("making fetch to", url)

    fetch(url)
        .then(resp=>{return resp.json()})
        .then(json=>{
            console.log(json[0])

            document.getElementById("author").innerHTML = json[0].author
            document.getElementById("lines").innerHTML = json[0].lines.join("<br>");


    })

}

document.addEventListener("DOMContentLoaded", () => {
  console.log("Hello World!");
});
