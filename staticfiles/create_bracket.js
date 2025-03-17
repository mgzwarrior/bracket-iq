// create_bracket.js
document.getElementById('seedlist').addEventListener('change', function() {
    var seedlistId = this.value;
    fetch('/get_teams/' + seedlistId)
        .then(response => response.json())
        .then(data => {
            for (var i = 1; i <= 68; i++) {
                var team1Select = document.getElementById('game' + i + 'team1');
                var team2Select = document.getElementById('game' + i + 'team2');
                data.teams.forEach(function(team) {
                    var option = document.createElement('option');
                    option.value = team.id;
                    option.text = team.name;
                    team1Select.appendChild(option.cloneNode(true));
                    team2Select.appendChild(option.cloneNode(true));
                });
            }
        });
});