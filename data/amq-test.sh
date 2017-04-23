function amq_test {
    split_dir=`realpath "${1}"`
    output_dir=`realpath "${2}"`
    build_size=$3
    pattern=$4
    index_dir="${output_dir}/${build_size}"

    test_size=100
    to_test=$(find ${split_dir}/$build_size/additional -type l -name "${pattern}" -exec readlink {} \; | shuf -n $test_size | xargs realpath)

    amq --workon "${index_dir}" use origin
    amq-test -q precision `echo ${to_test}` > "${index_dir}/test_${add_size}.log"
}


if [[ $# -ne 2 ]]; then
    echo "Usage: bash $0 <input-dir> <output-dir>"
else
    pattern='*.fasta'
    
    for build_size in {100..1000..100}
    do
        amq_test $1 $2 $build_size "${pattern}"
    done;
fi